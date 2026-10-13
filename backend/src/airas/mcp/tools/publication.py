import asyncio
from pathlib import Path
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
from airas.research_record.verify.verify_paper import verify_paper
from airas.research_record.verify.verify_record import verify_record
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

    A local clone must hold `.research/record.json` (every AIRAS
    repository ships one; `preregister_record` fills it) — a missing
    record fails the check. Runs both `verify_record` and
    `verify_paper_values` checks before handing out a PDF, including the
    provenance cross-check unless `check_provenance=False`. The
    record's verification lands under `record` (every failure is a line
    in its `problems`) and the build under `build`. On failure `ok`
    is false and no PDF is written to `output_path` — so a PDF this tool
    hands out states verified, provenance-backed numbers.
    """
    refresh_environment()

    if local_path:
        record = await verify_record(
            local_path,
            check_provenance=check_provenance,
            require_provenance=False,
            require_history=False,
            store_factory=_output_store,
        )
        paper = await verify_paper(local_path, latex_template_name)
        build = await asyncio.to_thread(
            build_paper,
            local_path,
            latex_template_name,
            output_path if record.ok and paper.ok else None,
        )
        ok = record.ok and paper.ok and build.ok
        if output_path and not ok:
            Path(output_path).unlink(missing_ok=True)
            build = build.model_copy(update={"pdf_path": None})
        return {
            **paper.model_dump(),
            "ok": ok,
            "record": record.model_dump(),
            "build": build.model_dump(),
            "pdf": build.pdf_path if ok else None,
            "problems": paper.problems
            + (["the LaTeX build failed (see build)"] if not build.ok else []),
        }
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


@mcp.tool()
async def verify_paper_values(
    local_path: str,
    latex_template_name: LATEX_TEMPLATE_NAME = "mdpi",
    citation_verifier_model: str | None = None,
) -> dict[str, Any]:
    """Check the paper's values, claims, tables, charts and citations.

    Generated files must match their regeneration from the record and run
    outputs. Every cited key and passage must belong to a registered source.
    `unverified`, `uncited_sources` and `unsupported_citations` are review
    items; citations without a current judgment fail the check.

    With `citation_verifier_model`, judge unjudged passage citations first
    and commit their judgments. Rewriting citing text requires a new
    judgment. Requires an LLM provider key when a model is given.

    Use `verify_record` separately for declaration consistency, run outputs,
    git history, provenance and implementation reviews. Both checks must
    pass before publication. This tool does not build a PDF.
    """
    refresh_environment()
    verification = await verify_paper(
        local_path,
        latex_template_name,
        citation_verifier_model=citation_verifier_model,
        litellm_client=_litellm_client() if citation_verifier_model else None,
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
