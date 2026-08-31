from __future__ import annotations

import math
import re
from pathlib import Path
from typing import Any

from pydantic import ValidationError

from airas.core.types.latex import LATEX_TEMPLATE_NAME
from airas.core.types.paper_values import (
    PaperTables,
    PaperValues,
    PaperValuesVerificationReport,
    ProvenanceCheckResult,
    ValueDeclaration,
)
from airas.usecases.publication.paper_values.charts import (
    chart_result_dirs,
    verify_charts,
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
from airas.usecases.publication.paper_values.tables import (
    TABLES_DIR_NAME,
    TABLES_JSON_FILENAME,
    render_table_tex,
    table_result_dirs,
    table_tex_relpath,
)

_UNVERIFIED_RE = re.compile(r"\\unverified\{([^{}]*)\}")
_AIRASVAL_RE = re.compile(r"\\airasval\{([^{}]*)\}")


def _strip_comment(line: str) -> str:
    """Drop a TeX comment, honouring backslash escapes.

    A % starts a comment unless escaped by an odd number of preceding
    backslashes: \\% is a literal percent sign, but \\\\% is a line
    break followed by a comment. A lookbehind for one backslash gets
    the second case wrong, so the parity is counted explicitly.
    """
    search_from = 0
    while True:
        at = line.find("%", search_from)
        if at == -1:
            return line
        backslashes = 0
        before = at - 1
        while before >= 0 and line[before] == "\\":
            backslashes += 1
            before -= 1
        if backslashes % 2 == 0:
            return line[:at]
        search_from = at + 1


def _scan_main_tex(main_tex: str) -> tuple[list[str], list[str]]:
    """Collect \\unverified contents and referenced \\airasval keys."""
    unverified: list[str] = []
    used_keys: list[str] = []
    for raw_line in main_tex.splitlines():
        line = _strip_comment(raw_line)
        unverified.extend(m.group(1) for m in _UNVERIFIED_RE.finditer(line))
        used_keys.extend(
            m.group(1)
            for m in _AIRASVAL_RE.finditer(line)
            if m.group(1) not in used_keys
        )
    return unverified, used_keys


def _verify_tables(latex_dir: Path, metrics_data: dict[str, Any]) -> list[str]:
    """Regenerate every declared table and reject undeclared table files.

    The unregistered-file check matters as much as the diff: without it a
    hand-written tables/<name>.tex could be \\input alongside the
    generated ones and carry any numbers at all.
    """
    problems: list[str] = []
    tables_json_path = latex_dir / TABLES_JSON_FILENAME
    registered: set[str] = set()
    if tables_json_path.is_file():
        try:
            tables = PaperTables.model_validate_json(
                tables_json_path.read_text(encoding="utf-8")
            )
        except ValidationError as e:
            return [f"{TABLES_JSON_FILENAME}: {e}"]
        for spec in tables.tables:
            registered.add(f"{spec.key}.tex")
            relpath = table_tex_relpath(spec.key)
            table_path = latex_dir / relpath
            if not table_path.is_file():
                problems.append(
                    f"{relpath} is missing (compute_paper_tables writes it)"
                )
                continue
            try:
                expected = render_table_tex(spec, metrics_data)
            except ValueError as e:
                problems.append(f"{relpath}: {e}")
                continue
            if table_path.read_text(encoding="utf-8") != expected:
                problems.append(
                    f"{relpath} differs from its regeneration (manual edit?)"
                )
    tables_dir = latex_dir / TABLES_DIR_NAME
    if tables_dir.is_dir():
        # Recursive: \input reaches any depth, so a hand-written table in
        # a subdirectory must not slip past the declaration check.
        for table_path in sorted(tables_dir.rglob("*.tex")):
            relative = table_path.relative_to(tables_dir).as_posix()
            if relative not in registered:
                problems.append(
                    f"{TABLES_DIR_NAME}/{relative} is not declared in "
                    f"{TABLES_JSON_FILENAME} — table files here must come "
                    "from compute_paper_tables"
                )
    return problems


def verify_paper_values(
    local_repo_path: str,
    latex_template_name: LATEX_TEMPLATE_NAME,
) -> PaperValuesVerificationReport:
    """Recompute every stated value from the run outputs and compare.

    Checks: values.json equals a recomputation from .research/results/
    (so a tampered record surfaces), values.tex is byte-identical to a
    regeneration (so manual edits to the macro table surface), every
    \\airasval key main.tex references is defined, every declared table
    under tables/ matches its regeneration from tables.json (and no
    undeclared table file exists there), and every chart under
    .research/results/chart/ matches a re-render of its declared spec.
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
                mismatches.extend(_verify_tables(latex_dir, metrics_data))
                mismatches.extend(verify_charts(str(root), metrics_data))

    return PaperValuesVerificationReport(
        ok=(
            not missing_files
            and values_match
            and values_tex_match
            and not undefined_keys
            and not mismatches
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
    """The results directories the paper draws data from.

    Values, tables, and charts all count: a run whose numbers only appear
    in a table or a chart still needs its metrics provenance-checked.
    """
    root = Path(local_repo_path).expanduser().resolve()
    latex_dir = root / ".research" / "latex" / latex_template_name
    try:
        metrics_data = load_metrics_data(str(root))
    except ValueError:
        return set()

    dirs: set[str] = set()
    try:
        stored = PaperValues.model_validate_json(
            (latex_dir / VALUES_JSON_FILENAME).read_text(encoding="utf-8")
        )
        declarations = [
            ValueDeclaration.model_validate(v.model_dump()) for v in stored.values
        ]
        dirs |= used_result_dirs(declarations, metrics_data)
    except (OSError, ValidationError, ValueError):
        pass
    try:
        tables = PaperTables.model_validate_json(
            (latex_dir / TABLES_JSON_FILENAME).read_text(encoding="utf-8")
        )
        dirs |= table_result_dirs(tables)
    except (OSError, ValidationError, ValueError):
        pass
    dirs |= chart_result_dirs(str(root), metrics_data)
    return dirs


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
