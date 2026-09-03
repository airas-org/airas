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
from airas.usecases.verification.record_gate import record_full_report

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
    global _seyval_client
    if _seyval_client is None:
        _seyval_client = SeyvalClient(
            async_session=httpx.AsyncClient(timeout=60.0, follow_redirects=True)
        )
        atexit.register(_close_seyval_client)
    return _seyval_client


def detect_templates(local_repo_path: str) -> list[str]:
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
    require_history: bool = True,
) -> list[str]:
    failures: list[str] = []
    if not merged.get("ok"):
        failures.append(
            "the combined LaTeX build and record verification reports "
            "ok=false (see the report for mismatches, undefined keys, "
            "citations, and figures)"
        )

    configured = bool(merged.get("paper_values_configured"))
    if require_paper_values and not configured:
        failures.append(
            "record.json is missing: the paper does not use the canonical-"
            "record system, so its claims and numbers cannot be verified "
            "(preregister_record creates it)"
        )

    paper_values = merged.get("paper_values") or {}
    if require_history and configured:
        if paper_values.get("append_only") == "unavailable":
            failures.append(
                "record.json's append-only history could not be checked "
                "(shallow clone or no git history) — CI must check out with "
                "fetch-depth: 0"
            )

    # The provenance cross-check runs at the results stage only: before any
    # run exists there is nothing to cross-check.
    if require_provenance and configured and paper_values.get("stage") == "results":
        provenance = paper_values.get("provenance")
        if provenance is None:
            failures.append(
                "the provenance cross-check did not run (record.json "
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
    require_history: bool,
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
    failures = gate_failures(
        merged, require_paper_values, require_provenance, require_history
    )
    if failures:
        # The artifact of a failed run must not contain a PDF: whatever is
        # in the artifact will be treated as "the paper".
        pdf_path.unlink(missing_ok=True)
    paper_values = merged.get("paper_values") or {}
    return {
        "template": template,
        "ok": not failures,
        "failures": failures,
        "pdf": str(pdf_path) if not failures and pdf_path.is_file() else None,
        "unverified": paper_values.get("unverified", []),
        "unverified_claims": paper_values.get("unverified_claims", []),
        "report": merged,
    }


async def run_paper_gate(
    local_repo_path: str,
    templates: list[str],
    output_dir: str,
    check_provenance: bool = True,
    require_paper_values: bool = True,
    require_provenance: bool = True,
    require_history: bool = True,
    seyval_client_factory: Callable[[], SeyvalClient] = _default_seyval_client,
) -> dict[str, Any]:
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
            require_history,
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


RECORD_REPORT_FILENAME = "record-verification-report.json"


async def run_record_gate(
    local_repo_path: str,
    output_dir: str,
    check_provenance: bool = True,
    require_provenance: bool = True,
    require_history: bool = True,
    seyval_client_factory: Callable[[], SeyvalClient] = _default_seyval_client,
) -> dict[str, Any]:
    """The check that guards the protected branch.

    Everything the paper gate does except the compile, so it can be required
    on every commit — including the ones that build the experiment code and
    import run outputs, which is exactly the window in which an unguarded
    branch would matter most. No LaTeX is installed for it.

    A repository with no record.json passes: there is nothing to contradict
    yet. A repository with a paper is held to more — its numbers must match
    the record, and it must *have* a record, since a paper without one has
    no verifiable number in it. `require_provenance` applies once runs
    exist, so the early pass does not quietly widen into "results without
    provenance are fine".
    """
    out = Path(output_dir).expanduser().resolve()
    out.mkdir(parents=True, exist_ok=True)
    # Turning the check off is a decision not to require it. Letting the two
    # disagree only produces "the provenance check did not run" on a run
    # that was told not to run it.
    require_provenance = require_provenance and check_provenance

    templates = detect_templates(local_repo_path)
    # No paper: one pass over the record alone.
    targets: list[str | None] = list(templates) or [None]
    results: list[dict[str, Any]] = []
    for template in targets:
        report = await record_full_report(
            local_repo_path,
            check_provenance,
            seyval_client_factory,
            cast(LATEX_TEMPLATE_NAME, template) if template else None,
        )
        merged = merge_paper_values_report({"ok": report.ok}, report)
        failures = gate_failures(
            merged,
            # A paper without a record has no verifiable number in it.
            require_paper_values=template is not None,
            require_provenance=require_provenance,
            require_history=require_history,
        )
        results.append(
            {
                "template": template,
                "ok": not failures,
                "failures": failures,
                "stage": report.stage,
                "unverified_claims": report.unverified_claims,
                "unverified": report.unverified,
                "report": merged,
            }
        )

    summary: dict[str, Any] = {
        "ok": all(r["ok"] for r in results),
        "papers": templates,
        "results": results,
    }
    # Flattened for a reader who wants the verdict without walking results.
    summary["failures"] = [
        (f"{r['template']}: {f}" if r["template"] else f)
        for r in results
        for f in r["failures"]
    ]
    summary["stage"] = results[0]["stage"]
    summary["unverified_claims"] = results[0]["unverified_claims"]
    (out / RECORD_REPORT_FILENAME).write_text(
        json.dumps(summary, indent=2, ensure_ascii=False, default=str) + "\n",
        encoding="utf-8",
    )
    return summary
