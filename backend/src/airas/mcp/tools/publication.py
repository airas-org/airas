"""Paper writing and publication."""

import asyncio
from typing import Any, Literal
from urllib.parse import urlencode

from airas.cli import DEFAULT_DASHBOARD_PORT
from airas.core.credentials import refresh_environment
from airas.core.llm_config import uniform_llm_mapping
from airas.core.types.experiment_code import ExperimentCode
from airas.core.types.experiment_history import ExperimentHistory
from airas.core.types.github import GitHubConfig
from airas.core.types.latex import LATEX_TEMPLATE_NAME
from airas.core.types.paper import PaperContent
from airas.core.types.research_hypothesis import ResearchHypothesis
from airas.core.types.research_study import ResearchStudy
from airas.dashboard.launcher import (
    dashboard_url,
    is_dashboard_running,
    start_dashboard,
)
from airas.mcp.app import mcp
from airas.mcp.context import (
    _dump,
    _github_client,
    _litellm_client,
    _output_store,
)
from airas.research_record.store import (
    load_record,
)
from airas.usecases.literature.bibliography import (
    render_references_bib,
)
from airas.usecases.publication.compile_latex_subgraph.compile_latex_subgraph import (
    CompileLatexLLMMapping,
    CompileLatexSubgraph,
)
from airas.usecases.publication.generate_latex_subgraph.generate_latex_subgraph import (
    GenerateLatexLLMMapping,
    GenerateLatexSubgraph,
)
from airas.usecases.publication.open_in_overleaf_subgraph.nodes.collect_latex_project_files import (
    collect_latex_project_files,
)
from airas.usecases.publication.verify_paper import (
    PaperVerification,
    verify_latex_build,
    verify_paper,
)
from airas.usecases.writers.generate_bibfile_subgraph.generate_bibfile_subgraph import (
    GenerateBibfileSubgraph,
)
from airas.usecases.writers.write_subgraph.write_subgraph import (
    WriteLLMMapping,
    WriteSubgraph,
)


@mcp.tool()
async def generate_bibfile(
    research_study_list: list[dict[str, Any]] | None = None,
    local_path: str | None = None,
) -> str:
    """Generate a BibTeX references file from research studies.

    With `local_path`, the .bib is rendered from the repository's registered
    literature — the same bytes `register_sources` wrote and the gate
    regenerates. Otherwise `research_study_list` should be the output of
    `retrieve_papers`. Returns the .bib content used by `generate_paper` and
    `generate_latex`. No API keys required.
    """
    if local_path:
        return render_references_bib(load_record(local_path).active_literature())
    studies = [
        ResearchStudy.model_validate(study) for study in research_study_list or []
    ]
    result = (
        await GenerateBibfileSubgraph()
        .build_graph()
        .ainvoke({"research_study_list": studies})
    )
    return result["references_bib"]


@mcp.tool()
async def generate_paper(
    research_hypothesis: dict[str, Any],
    experiment_history: dict[str, Any],
    experiment_code: dict[str, Any],
    research_study_list: list[dict[str, Any]],
    references_bib: str,
    model: str,
    writing_refinement_rounds: int = 2,
) -> dict[str, Any]:
    """Write the paper content from the completed research (backend LLM).

    Takes the hypothesis, experiment history, experiment code, related
    studies, and the BibTeX file (from `generate_bibfile`), and produces
    structured paper content (title, abstract, sections). Pass the result
    to `generate_latex`. `model` (required) is the LLM to use — call
    `get_available_llms` to list valid models. Requires an LLM provider API
    key — without one, use
    `get_generation_prompt(step="paper_writing", ...)` and author the paper
    yourself in one pass with the same curated prompt.
    """
    result = (
        await WriteSubgraph(
            litellm_client=_litellm_client(),
            paper_content_refinement_iterations=writing_refinement_rounds,
            llm_mapping=uniform_llm_mapping(WriteLLMMapping, model),
        )
        .build_graph()
        .ainvoke(
            {
                "research_hypothesis": ResearchHypothesis.model_validate(
                    research_hypothesis
                ),
                "experiment_history": ExperimentHistory.model_validate(
                    experiment_history
                ),
                "experiment_code": ExperimentCode.model_validate(experiment_code),
                "research_study_list": [
                    ResearchStudy.model_validate(study) for study in research_study_list
                ],
                "references_bib": references_bib,
            }
        )
    )
    return _dump(result["paper_content"])


@mcp.tool()
async def generate_latex(
    paper_content: dict[str, Any],
    references_bib: str,
    model: str,
    latex_template_name: LATEX_TEMPLATE_NAME = "mdpi",
) -> str:
    """Convert paper content into a full LaTeX document (backend LLM).

    `paper_content` should be the output of `generate_paper`. Available
    templates: "mdpi", "iclr2024", "agents4science_2025". Write the returned
    LaTeX to `.research/latex/{template}/main.tex` in your local clone of
    the experiment repository and push it with git, then build the PDF with
    `compile_latex` and/or hand it over with `open_in_overleaf`. `model`
    (required) is the LLM to use — call `get_available_llms` to list valid
    models. Requires an LLM provider API key and GH_PERSONAL_ACCESS_TOKEN —
    without them, use `get_generation_prompt(step="latex_conversion", ...)`
    and do the conversion yourself with the template from your local clone.
    """
    result = (
        await GenerateLatexSubgraph(
            litellm_client=_litellm_client(),
            github_client=_github_client(),
            latex_template_name=latex_template_name,
            llm_mapping=uniform_llm_mapping(GenerateLatexLLMMapping, model),
        )
        .build_graph()
        .ainvoke(
            {
                "paper_content": PaperContent.model_validate(paper_content),
                "references_bib": references_bib,
            }
        )
    )
    return result["latex_text"]


@mcp.tool()
async def compile_latex(
    github_owner: str,
    repository_name: str,
    branch_name: str,
    model: str,
    latex_template_name: LATEX_TEMPLATE_NAME = "mdpi",
    github_actions_agent: Literal["claude_code", "open_code"] = "claude_code",
) -> dict[str, Any]:
    """Build the paper PDF on GitHub Actions (asynchronous).

    One of the two publication exits after main.tex has been pushed to
    `.research/latex/{template}/` (the other is `open_in_overleaf`; they
    are independent and can both be used).
    Dispatches the LaTeX compilation workflow for the pushed sources.
    The workflow materializes every PDF under `.research/results/` and
    `.research/diagrams/` into the template's `images/` with the directory
    structure preserved, so figures need only be pushed, not pre-staged.
    Returns as soon as the dispatch is accepted, which is not a
    compile result — `paper_url` is where the PDF will land if the run
    succeeds, so track the run with `get_workflow_runs`, and use
    `verify_latex` to find out whether the document is actually sound.
    `model` (required) is forwarded to the compilation workflow as the
    coding-agent model (`model_name`) — call `get_available_llms` to list
    valid models. Requires GH_PERSONAL_ACCESS_TOKEN.
    """
    result = (
        await CompileLatexSubgraph(
            github_client=_github_client(),
            latex_template_name=latex_template_name,
            github_actions_agent=github_actions_agent,
            llm_mapping=uniform_llm_mapping(CompileLatexLLMMapping, model),
        )
        .build_graph()
        .ainvoke(
            {
                "github_config": GitHubConfig(
                    github_owner=github_owner,
                    repository_name=repository_name,
                    branch_name=branch_name,
                )
            }
        )
    )
    return {
        "compile_latex_dispatched": result["compile_latex_dispatched"],
        "paper_url": result["paper_url"],
    }


@mcp.tool()
async def verify_latex(
    github_owner: str = "",
    repository_name: str = "",
    branch_name: str = "",
    latex_template_name: LATEX_TEMPLATE_NAME = "mdpi",
    local_path: str | None = None,
    output_path: str | None = None,
    check_provenance: bool = True,
) -> dict[str, Any]:
    """Compile the paper locally and report whether it is actually sound.

    Use this before `open_in_overleaf` or `compile_latex` — those produce a
    link and a dispatch receipt, neither of which tells you the document
    built. This one builds it and answers the questions that decide whether
    the paper is publishable: did a PDF come out (`compiled`, `page_count`),
    do any citations render as `?` (`undefined_citations` — the usual cause
    is writing main.tex without also writing the generated bibliography to
    `.research/latex/{template}/references.bib`, whose shipped version is a
    single placeholder entry), do any `\\ref`s render as `??`
    (`undefined_references`), and is any figure referenced but absent
    (`missing_figures`). `ok` is true only when all of those are clean and
    `errors` — the `!` lines from the log, which is where a missing package
    or a broken environment shows up — is empty too.

    It compiles exactly the file set `open_in_overleaf` would export, so
    what is checked is what would be shipped. The toolchain is still the
    local one — Overleaf builds its own TeX Live image through latexmk — so
    read the two verdicts differently: `ok=False` is a property of the
    document and will follow it anywhere, while `ok=True` says this machine
    built it, not that Overleaf will. A package installed there but not
    here is the likely way the two disagree.

    Pass `local_path` — the absolute path of your local clone — to check the
    working tree with no push and no API keys. Otherwise pass
    `github_owner`/`repository_name`/`branch_name` to check what was pushed
    (requires GH_PERSONAL_ACCESS_TOKEN).

    Pass `output_path` to keep the PDF this build produced — the build
    directory is temporary otherwise, and `pdf_path` in the result says
    where it landed. For a Japanese paper that is the only way to get a PDF
    at all: `compile_latex` runs pdflatex on GitHub Actions, which cannot
    typeset CJK.

    Requires a local TeX distribution. A Japanese document is built with
    lualatex (`texlive-luatex`, `texlive-lang-japanese`); everything else
    with pdflatex.

    When checking a local clone of a paper that uses the canonical-record
    system (a `.research/record.json` created by `preregister_record`
    exists), the record is verified too — the same checks as
    `verify_paper_values`: declarations, append-only history, value/
    table/chart recomputation, claim flags, and (unless
    `check_provenance=False`) the Seyval provenance cross-check. The
    record's verification lands under `record` (every failure is a line
    in its `problems`) and the build under `build`. On failure `ok`
    is false and no PDF is written to `output_path` — so a PDF this tool
    hands out states verified, provenance-backed numbers.
    """
    refresh_environment()

    if local_path:
        verification = await _verify_paper(
            local_path, latex_template_name, output_path, check_provenance
        )
        return verification.model_dump()
    else:
        if not (github_owner and repository_name and branch_name):
            raise ValueError(
                "Provide local_path, or all of github_owner, repository_name "
                "and branch_name."
            )
        latex_files = await asyncio.to_thread(
            collect_latex_project_files,
            GitHubConfig(
                github_owner=github_owner,
                repository_name=repository_name,
                branch_name=branch_name,
            ),
            latex_template_name,
            _github_client(),
        )

    report = await asyncio.to_thread(
        verify_latex_build, latex_files, "main.tex", output_path
    )
    return report.model_dump()


async def _verify_paper(
    local_path: str,
    latex_template_name: LATEX_TEMPLATE_NAME,
    pdf_path: str | None,
    check_provenance: bool,
) -> PaperVerification:
    # The same verification CI runs, with this server's clients.
    # Unavailable provenance or history is surfaced here, not failed: only
    # CI requires the guarantee.
    return await verify_paper(
        local_path,
        latex_template_name,
        pdf_path=pdf_path,
        check_provenance=check_provenance,
        require_record=False,
        require_provenance=False,
        require_history=False,
        store_factory=_output_store,
    )


@mcp.tool()
async def verify_paper_values(
    local_path: str,
    latex_template_name: LATEX_TEMPLATE_NAME = "mdpi",
    check_provenance: bool = True,
) -> dict[str, Any]:
    """Check that everything the paper states is what was declared and measured.

    Verifies the canonical record `.research/record.json` end to end. At
    the prereg stage (no run outputs yet) it checks the declarations'
    internal consistency, that nothing realized exists prematurely, and
    the append-only history. Once results exist, the deterministic checks
    that decide `ok`: every declared value is recomputed from the run
    outputs under `.research/results/` and compared to the record's
    stored results (a tampered record surfaces as a mismatch),
    `values.tex` and `claims.tex` are regenerated and diffed byte-for-byte
    (`claims.tex` at the prereg stage too), every `\\airasval` key
    main.tex references must be
    declared, every table
    under `tables/` and every chart under `.research/results/chart/`
    must match a regeneration of its declaration (undeclared files fail),
    every results directory must belong to a declared run, the record's
    git history must be pure appends to the declaration section, and each
    claim's stored verified flag must be borne out by the recomputation:
    verified means every run under the claim has results. A claim that is
    merely not yet verified does not fail the check — only a stored flag
    the recomputation contradicts does.

    Unless `check_provenance=False`, the local metrics files are also
    cross-checked against the execution platform's stored run outputs
    (currently Seyval): each referenced results directory must be
    byte-identical to what the run *declared* for it in
    `.research/results/.provenance.json` (written by `import_run_outputs`)
    actually produced, that run must be completed, and its commit must be
    an ancestor of the local HEAD. Each check lists the other completed
    runs of the same commit (`sibling_run_ids`); review them — repeated
    executions mean the reported run was a choice. `provenance.status`
    "unavailable" is surfaced without failing the local checks.

    `unverified` lists every `\\unverified{...}` the author marked —
    review input, not a failure. Run this after any step that may edit
    main.tex (including compile agents), and treat the list as mandatory
    review items before publishing. `unsupported_citations` is the same
    kind of item: what the judge did not find borne out by the passage.
    `unjudged_citations` — citations no judgment covers as the text now
    stands — fail the check; `judge_citations` writes the judgments.
    """
    refresh_environment()
    verification = await _verify_paper(
        local_path, latex_template_name, None, check_provenance
    )
    return verification.model_dump()


@mcp.tool()
def open_in_overleaf(
    github_owner: str,
    repository_name: str,
    branch_name: str,
    latex_template_name: LATEX_TEMPLATE_NAME = "mdpi",
    local_path: str | None = None,
) -> dict[str, Any]:
    """Create a link that opens the paper in Overleaf for editing.

    One of the two publication exits for the paper (the other is
    `compile_latex`; they are independent and can both be used).
    Returns `overleaf_url`, which must be shown to the user as a clickable
    link. Opening it in a browser packages the LaTeX project (main.tex,
    bibliography, template assets, plus every figure PDF under
    `.research/results/` and `.research/diagrams/` mapped into `images/`)
    and submits it to Overleaf, creating a new project in the user's
    Overleaf account (login required; each click creates a new project).

    By default the project is read from the experiment repository on GitHub
    (main.tex must have been pushed; requires GH_PERSONAL_ACCESS_TOKEN,
    private repositories work). Pass `local_path` — the absolute path of your local
    clone — to read the working tree on disk instead: no push needed, and
    locally rendered figures are included as-is. Starts the local dashboard
    API in the background if needed.
    """
    refresh_environment()

    port = DEFAULT_DASHBOARD_PORT
    dashboard_status = "already_running"
    if not is_dashboard_running(port):
        start_dashboard(port)
        dashboard_status = "started"

    query: dict[str, str] = {
        "github_owner": github_owner,
        "repository_name": repository_name,
        "branch_name": branch_name,
        "latex_template_name": latex_template_name,
    }
    if local_path:
        query["local_path"] = local_path
    params = urlencode(query)
    overleaf_url = f"{dashboard_url(port)}/airas/v1/latex/overleaf?{params}"
    return {
        "overleaf_url": overleaf_url,
        "dashboard_status": dashboard_status,
        "note": (
            "Show this URL to the user as a clickable link. Opening it in a "
            "browser sends the paper's LaTeX sources to Overleaf and creates "
            "a new editable project there."
        ),
    }
