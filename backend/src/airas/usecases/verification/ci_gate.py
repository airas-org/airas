"""The `airas verify-paper` gate: verify a paper and build its PDF, or fail.

This is what the experiment repository's CI runs on push. It re-executes,
against one specific commit, the same verification the MCP tools run
locally — value recomputation, values.tex regeneration diff, undefined
\\airasval keys, and the Seyval provenance cross-check — then builds the
PDF from that same checked-out tree. Verification and artifact generation
are one step on purpose: the produced PDF cannot come from any state other
than the one that passed, so "the paper" can be defined as "the artifact
of a green run".

Local runs of `verify_latex` remain the fast feedback loop; this gate is
the judgement an agent cannot perform on its own behalf, because it runs
where the agent cannot interfere. Accordingly it is stricter than the
local check: a provenance status of "unavailable" (no credentials,
unregistered repository, network) fails the gate rather than warning,
since an unverifiable paper and an unverified paper must not ship.
"""

from __future__ import annotations

import asyncio
import atexit
import json
import logging
from pathlib import Path
from typing import Any, Callable, cast, get_args

import httpx

from airas.core.types.latex import LATEX_TEMPLATE_NAME
from airas.infra.seyval_client import SeyvalClient
from airas.usecases.publication.nodes.verify_latex_build import verify_latex_build
from airas.usecases.publication.open_in_overleaf_subgraph.nodes.collect_latex_project_files import (
    collect_latex_project_files_local,
)
from airas.usecases.publication.paper_values.verify import merge_paper_values_report
from airas.usecases.verification.paper_verification import paper_values_full_report

logger = logging.getLogger(__name__)

REPORT_FILENAME = "verification-report.json"

_seyval_client: SeyvalClient | None = None


def _close_seyval_client() -> None:
    # atexit runs after every event loop is gone, so a fresh one is fine;
    # never let cleanup turn a finished gate run into a failure.
    if _seyval_client is not None:
        try:
            asyncio.run(_seyval_client.aclose())
        except Exception:  # pragma: no cover - best-effort cleanup
            pass


def _default_seyval_client() -> SeyvalClient:
    """A process-lifetime Seyval client for the CLI gate.

    SeyvalClient requires its HTTP session by injection; the MCP server
    supplies its own, and this is the CLI's. Cached because the factory
    is called per template and the sessions are reusable; closed at
    process exit so the connection pool does not leak.
    """
    global _seyval_client
    if _seyval_client is None:
        _seyval_client = SeyvalClient(
            async_session=httpx.AsyncClient(timeout=60.0, follow_redirects=True)
        )
        atexit.register(_close_seyval_client)
    return _seyval_client


def detect_templates(local_repo_path: str) -> list[str]:
    """The templates under .research/latex/ that hold a written paper."""
    latex_root = Path(local_repo_path).expanduser().resolve() / ".research" / "latex"
    if not latex_root.is_dir():
        return []
    known = set(get_args(LATEX_TEMPLATE_NAME))
    found = []
    for path in sorted(latex_root.iterdir()):
        if not (path / "main.tex").is_file():
            continue
        if path.name not in known:
            logger.warning(f"Skipping unknown LaTeX template directory: {path.name}")
            continue
        found.append(path.name)
    return found


def gate_failures(
    merged: dict[str, Any],
    require_paper_values: bool,
    require_provenance: bool,
) -> list[str]:
    """Why this paper must not ship — empty means the gate passes.

    `merged` is a LaTeX build report with the paper-values report folded
    in (`merge_paper_values_report`). The extra strictness over `ok` is
    the CI policy: paper values must be configured at all, and the
    provenance cross-check must have run and answered "verified" —
    locally "unavailable" only warns, but a gate that shrugs at an
    unverifiable paper is not a gate.
    """
    failures: list[str] = []
    if not merged.get("ok"):
        failures.append(
            "the combined LaTeX build and paper-value verification reports "
            "ok=false (see the report for mismatches, undefined keys, "
            "citations, and figures)"
        )

    configured = bool(merged.get("paper_values_configured"))
    if require_paper_values and not configured:
        failures.append(
            "values.json is missing: the paper does not use the declared-"
            "values system, so its numbers cannot be verified "
            "(compute_paper_values writes it)"
        )

    if require_provenance and configured:
        paper_values = merged.get("paper_values") or {}
        provenance = paper_values.get("provenance")
        if provenance is None:
            failures.append(
                "the provenance cross-check did not run (values.json "
                "references no results directories, or the check was "
                "disabled)"
            )
        elif provenance.get("status") != "verified":
            failures.append(
                f"provenance {provenance.get('status')}: "
                f"{provenance.get('detail') or 'see provenance.checks'}"
            )
    return failures


async def _gate_one_template(
    local_repo_path: str,
    template: LATEX_TEMPLATE_NAME,
    output_dir: Path,
    check_provenance: bool,
    require_paper_values: bool,
    require_provenance: bool,
    seyval_client_factory: Callable[[], SeyvalClient],
) -> dict[str, Any]:
    report = await paper_values_full_report(
        local_repo_path, template, check_provenance, seyval_client_factory
    )
    latex_files = await asyncio.to_thread(
        collect_latex_project_files_local, local_repo_path, template
    )
    pdf_path = output_dir / f"{template}.pdf"
    build = await asyncio.to_thread(
        verify_latex_build, latex_files, "main.tex", str(pdf_path)
    )
    merged = merge_paper_values_report(build.model_dump(), report)
    failures = gate_failures(merged, require_paper_values, require_provenance)
    if failures:
        # The artifact of a failed run must not contain a PDF: whatever is
        # in the artifact will be treated as "the paper".
        pdf_path.unlink(missing_ok=True)
    return {
        "template": template,
        "ok": not failures,
        "failures": failures,
        "pdf": str(pdf_path) if not failures and pdf_path.is_file() else None,
        "unverified": (merged.get("paper_values") or {}).get("unverified", []),
        "report": merged,
    }


async def run_paper_gate(
    local_repo_path: str,
    templates: list[str],
    output_dir: str,
    check_provenance: bool = True,
    require_paper_values: bool = True,
    require_provenance: bool = True,
    seyval_client_factory: Callable[[], SeyvalClient] = _default_seyval_client,
) -> dict[str, Any]:
    """Gate every written template; write PDFs and the report to `output_dir`.

    Returns `{"ok": bool, "templates": [...]}`; `ok` is true only if every
    template passed. The full report is also written to
    `verification-report.json` inside `output_dir`, whether or not the
    gate passed, so a failed CI run still leaves something to debug from.
    """
    out = Path(output_dir).expanduser().resolve()
    out.mkdir(parents=True, exist_ok=True)

    results = [
        await _gate_one_template(
            local_repo_path,
            cast(LATEX_TEMPLATE_NAME, template),
            out,
            check_provenance,
            require_paper_values,
            require_provenance,
            seyval_client_factory,
        )
        for template in templates
    ]

    summary = {"ok": all(r["ok"] for r in results), "templates": results}
    (out / REPORT_FILENAME).write_text(
        json.dumps(summary, indent=2, ensure_ascii=False, default=str) + "\n",
        encoding="utf-8",
    )
    return summary
