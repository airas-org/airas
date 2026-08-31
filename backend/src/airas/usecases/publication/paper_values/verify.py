from __future__ import annotations

import math
import re
from pathlib import Path
from typing import Any

from pydantic import ValidationError

from airas.core.types.latex import LATEX_TEMPLATE_NAME
from airas.core.types.paper_values import (
    PaperValues,
    PaperValuesVerificationReport,
    ProvenanceCheckResult,
    ValueDeclaration,
)
from airas.usecases.publication.paper_values.compute import (
    compute_paper_values,
    load_metrics_data,
    used_result_dirs,
)
from airas.usecases.publication.paper_values.latex import (
    VALUES_JSON_FILENAME,
    VALUES_TEX_FILENAME,
    render_values_tex,
)

_UNVERIFIED_RE = re.compile(r"\\unverified\{([^{}]*)\}")
_AIRASVAL_RE = re.compile(r"\\airasval\{([^{}]*)\}")
_COMMENT_RE = re.compile(r"(?<!\\)%.*")


def _scan_main_tex(main_tex: str) -> tuple[list[str], list[str]]:
    """Collect \\unverified contents and referenced \\airasval keys."""
    unverified: list[str] = []
    used_keys: list[str] = []
    for raw_line in main_tex.splitlines():
        line = _COMMENT_RE.sub("", raw_line)
        unverified.extend(m.group(1) for m in _UNVERIFIED_RE.finditer(line))
        used_keys.extend(
            m.group(1)
            for m in _AIRASVAL_RE.finditer(line)
            if m.group(1) not in used_keys
        )
    return unverified, used_keys


def verify_paper_values(
    local_repo_path: str,
    latex_template_name: LATEX_TEMPLATE_NAME,
) -> PaperValuesVerificationReport:
    """Recompute every stated value from the run outputs and compare.

    Three checks: values.json equals a recomputation from
    .research/results/ (so a tampered record surfaces), values.tex is
    byte-identical to a regeneration (so manual edits to the macro table
    surface), and every \\airasval key main.tex references is defined.
    \\unverified contents are collected as review input. The provenance
    cross-check (a ProvenanceVerifier implementation) is a separate async
    step layered on by the callers via apply_provenance_result.
    """
    root = Path(local_repo_path).expanduser().resolve()
    latex_dir = root / ".research" / "latex" / latex_template_name
    values_json_path = latex_dir / VALUES_JSON_FILENAME
    values_tex_path = latex_dir / VALUES_TEX_FILENAME
    main_tex_path = latex_dir / "main.tex"

    missing_files = [
        str(path.relative_to(root))
        for path in (values_json_path, values_tex_path, main_tex_path)
        if not path.is_file()
    ]

    unverified: list[str] = []
    used_keys: list[str] = []
    if main_tex_path.is_file():
        unverified, used_keys = _scan_main_tex(
            main_tex_path.read_text(encoding="utf-8")
        )

    mismatches: list[str] = []
    undefined_keys: list[str] = []
    values_match = False
    values_tex_match = False
    if values_json_path.is_file():
        try:
            stored = PaperValues.model_validate_json(
                values_json_path.read_text(encoding="utf-8")
            )
            metrics_data = load_metrics_data(str(root))
        except (ValidationError, ValueError) as e:
            mismatches.append(str(e))
        else:
            defined = {v.key for v in stored.values}
            undefined_keys = [k for k in used_keys if k not in defined]
            declarations = [
                ValueDeclaration.model_validate(v.model_dump()) for v in stored.values
            ]
            try:
                recomputed = compute_paper_values(declarations, metrics_data)
            except ValueError as e:
                mismatches.append(str(e))
            else:
                for old, new in zip(stored.values, recomputed.values, strict=True):
                    if not math.isclose(
                        old.value, new.value, rel_tol=1e-9, abs_tol=1e-12
                    ):
                        mismatches.append(
                            f"{old.key}: stored {old.value} != recomputed {new.value}"
                        )
                    elif old.display != new.display:
                        mismatches.append(
                            f"{old.key}: stored display '{old.display}' != "
                            f"recomputed '{new.display}'"
                        )
                values_match = not mismatches
                if values_tex_path.is_file():
                    values_tex_match = values_tex_path.read_text(
                        encoding="utf-8"
                    ) == render_values_tex(recomputed)
                    if not values_tex_match:
                        mismatches.append(
                            f"{VALUES_TEX_FILENAME} differs from its "
                            "regeneration (manual edit?)"
                        )

    return PaperValuesVerificationReport(
        ok=(
            not missing_files
            and values_match
            and values_tex_match
            and not undefined_keys
        ),
        values_match=values_match,
        values_tex_match=values_tex_match,
        mismatches=mismatches,
        missing_files=missing_files,
        undefined_keys=undefined_keys,
        unverified=unverified,
    )


def referenced_result_dirs(
    local_repo_path: str,
    latex_template_name: LATEX_TEMPLATE_NAME,
) -> set[str]:
    """The results directories the stored values.json draws values from."""
    root = Path(local_repo_path).expanduser().resolve()
    values_json_path = (
        root / ".research" / "latex" / latex_template_name / VALUES_JSON_FILENAME
    )
    try:
        stored = PaperValues.model_validate_json(
            values_json_path.read_text(encoding="utf-8")
        )
        metrics_data = load_metrics_data(str(root))
    except (OSError, ValidationError, ValueError):
        return set()
    declarations = [
        ValueDeclaration.model_validate(v.model_dump()) for v in stored.values
    ]
    return used_result_dirs(declarations, metrics_data)


def apply_provenance_result(
    report: PaperValuesVerificationReport, provenance: ProvenanceCheckResult
) -> PaperValuesVerificationReport:
    """Fold a provenance cross-check into a verification report.

    A mismatch means the local metrics are not backed by any completed
    run in the platform's storage — the local copy cannot be trusted, so
    `ok` goes false. "unavailable" is surfaced but does not fail the
    local checks; callers that require the guarantee (CI) should treat it
    as a failure there.
    """
    report.provenance = provenance
    if provenance.status == "mismatch":
        report.ok = False
        report.mismatches.append(
            f"{provenance.source}: local metrics are not backed by stored "
            "run outputs — " + (provenance.detail or "see provenance.checks")
        )
    return report


def paper_values_configured(report: PaperValuesVerificationReport) -> bool:
    """Whether the paper opted into the value system (values.json exists)."""
    return not any(p.endswith(VALUES_JSON_FILENAME) for p in report.missing_files)


def merge_paper_values_report(
    latex_result: dict[str, Any],
    report: PaperValuesVerificationReport,
) -> dict[str, Any]:
    """Fold a value verification into a LaTeX build report.

    A paper that opted in must also pass the value checks for the build to
    count as `ok` — this is what makes "a PDF came out" imply "the numbers
    in it are the numbers that were measured".
    """
    latex_result["paper_values"] = report.model_dump()
    configured = paper_values_configured(report)
    latex_result["paper_values_configured"] = configured
    if configured:
        latex_result["ok"] = bool(latex_result.get("ok")) and report.ok
    return latex_result
