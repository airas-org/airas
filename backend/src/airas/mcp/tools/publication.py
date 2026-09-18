"""Paper writing and publication."""

import asyncio
from typing import Any
from urllib.parse import urlencode

from airas.core.credentials import refresh_environment
from airas.core.types.github import GitHubConfig
from airas.core.types.latex import LATEX_TEMPLATE_NAME
from airas.dashboard.launcher import (
    DEFAULT_DASHBOARD_PORT,
    dashboard_url,
    is_dashboard_running,
    start_dashboard,
)
from airas.mcp.app import mcp
from airas.mcp.context import (
    _github_client,
    _litellm_client,
    _output_store,
)
from airas.research_record.verify.verify_paper import PaperVerification, verify_paper
from airas.usecases.publication.build_paper import build_paper
from airas.usecases.publication.nodes.collect_latex_project_files import (
    collect_latex_project_files,
)


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

    Use this before `open_in_overleaf` or a push — those produce a
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
    where it landed. A Japanese paper's PDF comes from here or from the
    Publish Paper workflow (lualatex on both).

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
        build_paper, None, latex_template_name, output_path, latex_files=latex_files
    )
    return report.model_dump()


async def _verify_paper(
    local_path: str,
    latex_template_name: LATEX_TEMPLATE_NAME,
    pdf_path: str | None,
    check_provenance: bool,
    model: str | None = None,
) -> PaperVerification:
    # The same verification CI runs, with this server's clients.
    # Unavailable provenance or history is surfaced here, not failed: only
    # CI requires the guarantee.
    return await verify_paper(
        local_path,
        latex_template_name,
        pdf_path=pdf_path,
        build=build_paper,
        check_provenance=check_provenance,
        require_record=False,
        require_provenance=False,
        require_history=False,
        store_factory=_output_store,
        model=model,
        litellm_client=_litellm_client() if model else None,
    )


@mcp.tool()
async def verify_paper_values(
    local_path: str,
    latex_template_name: LATEX_TEMPLATE_NAME = "mdpi",
    check_provenance: bool = True,
    model: str | None = None,
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
    stands — fail the check. Pass `model` to have that model read each
    unjudged citation against its passage first; the judgments are written
    into the record and committed, so the same call then reports only what
    the model found unsupported. Re-run with `model` after rewriting a
    sentence that cites a passage. Requires an LLM provider key when `model`
    is given.
    """
    refresh_environment()
    verification = await _verify_paper(
        local_path, latex_template_name, None, check_provenance, model
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
