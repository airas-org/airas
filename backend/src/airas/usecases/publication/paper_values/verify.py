"""Verification of the record and of the paper that draws on it.

Two checks, on two sources of truth, and every value in the record traces
to one of them:

  A. What is already recorded is intact — git history. Every committed
     revision of record.json contains the one before it (containment); the
     declarations are internally sound; and each claim's declaration
     already existed, in this exact form, at the commit its runs executed.

  B. What is being appended is bound to the experiment and re-derivable —
     the platform's record and the files it stored. Each result names the
     execution the manifest names; its copies (metrics, inputs hash, the
     evaluator's report) equal the files; the declared run conditions match
     what the platform recorded; and `verified` is never stored as true
     where the recomputation finds otherwise.

`check_record` runs both. `verify_paper_record` adds the paper's own checks
on top (values.tex regeneration, declared tables, every \\airasval key
declared). The record gate calls `check_record` alone.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Literal

from pydantic import ValidationError

from airas.core.research_paths import RECORD_FILENAME, RECORD_PATH
from airas.core.types.latex import LATEX_TEMPLATE_NAME
from airas.core.types.paper_values import (
    ClaimStatus,
    PaperValuesVerificationReport,
    ProvenanceCheckResult,
    TableSpec,
)
from airas.core.types.research_record import ResearchRecord
from airas.core.types.run_provenance import (
    PROVENANCE_MANIFEST_PATH,
    RunProvenanceManifest,
)
from airas.infra.local_git import normalize_git_url, remote_origin_url
from airas.usecases.publication.paper_values.charts import (
    chart_result_dirs,
    verify_charts,
)
from airas.usecases.publication.paper_values.compute import (
    COMPARISON_KEY,
    RESULTS_DIR,
    load_metrics_data,
    resolve_paper_values,
    used_result_dirs,
)
from airas.usecases.publication.paper_values.latex import (
    VALUES_TEX_FILENAME,
    render_values_tex,
)
from airas.usecases.publication.paper_values.realize import (
    eval_inputs_ref,
    eval_report,
)
from airas.usecases.publication.paper_values.record import (
    all_claims,
    all_tables,
    load_record,
    record_consistency_problems,
    run_index,
    selected_result,
)
from airas.usecases.publication.paper_values.tables import (
    TABLES_DIR_NAME,
    render_table_tex,
    table_result_dirs,
    table_tex_relpath,
)
from airas.usecases.verification.record_history import (
    APPEND_ONLY_STATUS,
    compute_claim_status,
    record_append_only_status,
)
from airas.usecases.verification.seyval_provenance import load_provenance_manifest

_UNVERIFIED_RE = re.compile(r"\\unverified\{([^{}]*)\}")
_AIRASVAL_RE = re.compile(r"\\airasval\{([^{}]*)\}")


def _strip_comment(line: str) -> str:
    # A % starts a comment unless escaped by an odd number of preceding
    # backslashes: \% is a literal percent, \\% is a line break + comment.
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


def _verify_tables(
    latex_dir: Path, specs: list[TableSpec], metrics_data: dict[str, Any]
) -> list[str]:
    # The undeclared-file check matters as much as the diff: without it a
    # hand-written tables/<name>.tex could be \input alongside the
    # generated ones and carry any numbers at all.
    problems: list[str] = []
    registered: set[str] = set()
    for spec in specs:
        registered.add(f"{spec.key}.tex")
        relpath = table_tex_relpath(spec.key)
        table_path = latex_dir / relpath
        if not table_path.is_file():
            problems.append(f"{relpath} is missing (update_record writes it)")
            continue
        try:
            expected = render_table_tex(spec, metrics_data)
        except ValueError as e:
            problems.append(f"{relpath}: {e}")
            continue
        if table_path.read_text(encoding="utf-8") != expected:
            problems.append(f"{relpath} differs from its regeneration (manual edit?)")
    tables_dir = latex_dir / TABLES_DIR_NAME
    if tables_dir.is_dir():
        for table_path in sorted(tables_dir.rglob("*.tex")):
            relative = table_path.relative_to(tables_dir).as_posix()
            if relative not in registered:
                problems.append(
                    f"{TABLES_DIR_NAME}/{relative} is not declared in "
                    f"{RECORD_FILENAME} — table files here must come from "
                    "update_record"
                )
    return problems


# --------------------------------------------------------------------------
# B: what is being appended
# --------------------------------------------------------------------------


def params_problems(
    record: ResearchRecord, manifest: RunProvenanceManifest | None
) -> list[str]:
    """Did each run execute under the conditions it declared?

    The commit fixes the config files but not the dispatch, so a run
    declared as `mode=full` can be executed as `mode=pilot` with the tree
    untouched — a fifth of the planned scale, reported as if it were the
    whole thing. The manifest carries what the platform recorded for the
    dispatch (itself checked against the platform by the provenance step);
    the declaration is compared with that.

    A declared key the platform never mentions is reported only when the
    platform gave a complete parameter set. With overrides alone the
    absence is ambiguous: the run may have taken the value from a default
    the dispatch never had to restate.
    """
    problems: list[str] = []
    for run in run_index(record).values():
        declared = manifest.dirs.get(run.run_id) if manifest else None
        if declared is None or not run.params:
            continue
        resolved = declared.parameters or declared.overrides
        complete = bool(declared.parameters)
        for key, wanted in run.params.items():
            if key not in resolved:
                if complete:
                    problems.append(
                        f"run '{run.run_id}': declared '{key}={wanted}' but "
                        "the execution resolved no such parameter"
                    )
                continue
            if str(resolved[key]) != str(wanted):
                problems.append(
                    f"run '{run.run_id}': declared '{key}={wanted}' but "
                    f"executed '{key}={resolved[key]}'"
                )
    return problems


def result_problems(
    root: Path,
    record: ResearchRecord,
    metrics_data: dict[str, Any],
    manifest: RunProvenanceManifest | None,
) -> list[str]:
    """Is every value a result entry holds re-derivable from its source?

    A result is a set of copies: of the manifest (which execution, which
    commit), of the metrics file, of the inputs' hash, of the evaluator's
    report. Each is compared with what it claims to copy. Without this, a
    result appended by hand could carry numbers that no file, no manifest
    and no platform ever produced — and pass, because containment allows
    appends and the paper reads the files rather than the record.
    """
    problems: list[str] = []
    for run in run_index(record).values():
        result = selected_result(run)
        if result is None:
            continue
        rid = run.run_id

        declared = manifest.dirs.get(rid) if manifest else None
        if declared is None:
            problems.append(
                f"run '{rid}': the record holds a result but no readable "
                f"{PROVENANCE_MANIFEST_PATH} entry declares an execution for "
                "this directory"
            )
        else:
            if result.id != declared.execution_id:
                problems.append(
                    f"run '{rid}': the result's id {result.id!r} is not the "
                    f"manifest's execution {declared.execution_id!r}"
                )
            if result.commit != declared.commit_hash:
                problems.append(
                    f"run '{rid}': the result's commit {result.commit!r} is "
                    f"not the manifest's {declared.commit_hash!r}"
                )

        if rid in metrics_data and result.metrics != metrics_data[rid]:
            problems.append(
                f"run '{rid}': the result's metrics differ from "
                f"{RESULTS_DIR}/{rid}/metrics.json"
            )

        expected_inputs = eval_inputs_ref(root, rid)
        if (result.eval_inputs is None) != (expected_inputs is None) or (
            result.eval_inputs is not None
            and expected_inputs is not None
            and result.eval_inputs.model_dump() != expected_inputs.model_dump()
        ):
            problems.append(
                f"run '{rid}': the result's eval_inputs hash does not match "
                "the eval_inputs file in the results directory"
            )

        expected_eval = eval_report(root, rid)
        if (result.eval_report is None) != (expected_eval is None) or (
            result.eval_report is not None
            and expected_eval is not None
            and result.eval_report.model_dump() != expected_eval.model_dump()
        ):
            problems.append(
                f"run '{rid}': the result's eval_report differs from the "
                "evaluator's report in the results directory"
            )

        # The evaluator's own `inputs_sha256` is deliberately not compared
        # with `eval_inputs.sha256`. airas-eval hashes the *parsed* payload
        # in a canonical JSON form (sorted keys, no whitespace, its own type
        # coercion), while the record hashes the file's bytes, so the two
        # digests differ for every honest run. The evaluator's digest is
        # still carried verbatim — it names what the evaluator scored in the
        # evaluator's own terms — and the file hash is what the provenance
        # step holds against the platform's stored bytes.
    return problems


def verified_problems(record: ResearchRecord, statuses: list[ClaimStatus]) -> list[str]:
    """Claims stored as verified that the recomputation finds otherwise.

    A stored true is a fact the history must still bear out. The reverse —
    recomputed true, stored false — is not a problem: update_record has
    simply not run since the procedure completed.
    """
    recomputed = {s.id: s.verified for s in statuses}
    return [
        claim.id
        for _, claim in all_claims(record)
        if claim.verified and not recomputed.get(claim.id, False)
    ]


# --------------------------------------------------------------------------
# A + B together: the record's own verdict, shared by both entry points
# --------------------------------------------------------------------------


@dataclass
class RecordChecks:
    stage: Literal["prereg", "results"]
    mismatches: list[str] = field(default_factory=list)
    append_only: APPEND_ONLY_STATUS = "unavailable"
    append_only_problems: list[str] = field(default_factory=list)
    record_commits: list[str] = field(default_factory=list)
    claims: list[ClaimStatus] = field(default_factory=list)
    claim_status_match: bool = True
    undeclared_result_dirs: list[str] = field(default_factory=list)


def check_record(
    root: Path, record: ResearchRecord, metrics_data: dict[str, Any] | None
) -> RecordChecks:
    stage: Literal["prereg", "results"] = "results" if metrics_data else "prereg"
    checks = RecordChecks(stage=stage)
    manifest = load_provenance_manifest(root)

    # A — what is already recorded
    checks.mismatches.extend(record_consistency_problems(record))
    checks.append_only, checks.append_only_problems, checks.record_commits = (
        record_append_only_status(root, record)
    )

    if stage == "prereg":
        # Nothing measured yet, so nothing realized may exist.
        realized = [run.run_id for run in run_index(record).values() if run.results]
        realized += [c.id for _, c in all_claims(record) if c.verified]
        if realized:
            checks.mismatches.append(
                "record.json holds results but no run outputs exist "
                f"({', '.join(sorted(set(realized)))})"
            )
        checks.claims = compute_claim_status(record, set())
        return checks

    assert metrics_data is not None
    # B — what is being appended
    checks.mismatches.extend(params_problems(record, manifest))
    checks.mismatches.extend(result_problems(root, record, metrics_data, manifest))
    checks.mismatches.extend(verify_charts(record, str(root), metrics_data))
    declared_runs = set(run_index(record))
    checks.undeclared_result_dirs = sorted(
        d for d in metrics_data if d != COMPARISON_KEY and d not in declared_runs
    )
    checks.claims = compute_claim_status(record, set(metrics_data))
    drifted = verified_problems(record, checks.claims)
    checks.claim_status_match = not drifted
    if drifted:
        checks.mismatches.append(
            "claims stored as verified that the recomputation finds otherwise "
            f"({', '.join(drifted)})"
        )
    return checks


def record_ok(checks: RecordChecks) -> bool:
    return (
        not checks.mismatches
        and checks.append_only != "violated"
        and checks.claim_status_match
        and not checks.undeclared_result_dirs
    )


# --------------------------------------------------------------------------
# The paper on top
# --------------------------------------------------------------------------


def verify_paper_record(
    local_repo_path: str,
    latex_template_name: LATEX_TEMPLATE_NAME,
) -> PaperValuesVerificationReport:
    root = Path(local_repo_path).expanduser().resolve()
    latex_dir = root / ".research" / "latex" / latex_template_name
    record_file = root / RECORD_PATH
    values_tex_path = latex_dir / VALUES_TEX_FILENAME
    main_tex_path = latex_dir / "main.tex"

    unverified: list[str] = []
    used_keys: list[str] = []
    if main_tex_path.is_file():
        unverified, used_keys = _scan_main_tex(
            main_tex_path.read_text(encoding="utf-8")
        )

    record: ResearchRecord | None = None
    mismatches: list[str] = []
    if record_file.is_file():
        try:
            record = load_record(str(root))
        except (ValidationError, ValueError) as e:
            mismatches.append(f"{RECORD_PATH}: {e}")

    try:
        metrics_data: dict[str, Any] | None = load_metrics_data(str(root))
    except ValueError:
        metrics_data = None
    stage: Literal["prereg", "results"] = "results" if metrics_data else "prereg"

    required = [record_file, main_tex_path]
    if stage == "results":
        required.append(values_tex_path)
    missing_files = [str(p.relative_to(root)) for p in required if not p.is_file()]

    undefined_keys: list[str] = []
    values_match = False
    values_tex_match = False
    checks = RecordChecks(stage=stage)

    if record is not None:
        checks = check_record(root, record, metrics_data)
        mismatches.extend(checks.mismatches)

        if stage == "prereg":
            # A values.tex carried over without runs would put unverifiable
            # numbers in the PDF.
            values_match = True
            values_tex_match = True
            if values_tex_path.is_file():
                mismatches.append(
                    f"{VALUES_TEX_FILENAME} exists but no run outputs exist"
                )
            if (latex_dir / TABLES_DIR_NAME).is_dir():
                mismatches.append(f"{TABLES_DIR_NAME}/ exists but no run outputs exist")
        else:
            assert metrics_data is not None
            paper_values, undefined_keys = resolve_paper_values(
                record, metrics_data, used_keys
            )
            values_match = True
            if values_tex_path.is_file():
                origin = remote_origin_url(root)
                values_tex_match = values_tex_path.read_text(
                    encoding="utf-8"
                ) == render_values_tex(
                    paper_values,
                    normalize_git_url(origin) if origin else None,
                    checks.record_commits[-1] if checks.record_commits else None,
                )
                if not values_tex_match:
                    mismatches.append(
                        f"{VALUES_TEX_FILENAME} differs from its "
                        "regeneration (manual edit?)"
                    )
            mismatches.extend(
                _verify_tables(latex_dir, all_tables(record), metrics_data)
            )

    return PaperValuesVerificationReport(
        ok=(
            not missing_files
            and values_match
            and values_tex_match
            and not undefined_keys
            and not mismatches
            and checks.append_only != "violated"
            and checks.claim_status_match
            and not checks.undeclared_result_dirs
        ),
        stage=stage,
        values_match=values_match,
        values_tex_match=values_tex_match,
        mismatches=mismatches,
        missing_files=missing_files,
        undefined_keys=undefined_keys,
        append_only=checks.append_only,
        append_only_problems=checks.append_only_problems,
        record_commits=checks.record_commits,
        claims=checks.claims,
        claim_status_match=checks.claim_status_match,
        undeclared_result_dirs=checks.undeclared_result_dirs,
        unverified_claims=[s.id for s in checks.claims if not s.verified],
        unverified=unverified,
    )


def referenced_result_dirs(local_repo_path: str) -> set[str]:
    """The results directories the record or the paper draws data from."""
    try:
        record = load_record(local_repo_path)
        metrics_data = load_metrics_data(local_repo_path)
    except (ValidationError, ValueError):
        return set()

    dirs = used_result_dirs(record, metrics_data)
    dirs |= table_result_dirs(all_tables(record), metrics_data)
    dirs |= chart_result_dirs(record, metrics_data)
    return dirs


def apply_provenance_result(
    report: PaperValuesVerificationReport, provenance: ProvenanceCheckResult
) -> PaperValuesVerificationReport:
    # A mismatch means the local outputs are not backed by any completed
    # run in the platform's storage; "unavailable" is surfaced but only
    # fails in CI, which requires the guarantee.
    report.provenance = provenance
    if provenance.status == "mismatch":
        report.ok = False
        report.mismatches.append(
            f"{provenance.source}: local outputs are not backed by stored "
            "run outputs — " + (provenance.detail or "see provenance.checks")
        )
    return report


def paper_values_configured(report: PaperValuesVerificationReport) -> bool:
    """Whether the repository opted into the record system (record.json exists)."""
    return not any(p.endswith(RECORD_FILENAME) for p in report.missing_files)


def merge_paper_values_report(
    latex_result: dict[str, Any],
    report: PaperValuesVerificationReport,
) -> dict[str, Any]:
    # A paper that opted in must also pass the record checks for the build
    # to count as ok — this is what makes "a PDF came out" imply "the
    # numbers in it are the numbers that were measured".
    latex_result["paper_values"] = report.model_dump()
    configured = paper_values_configured(report)
    latex_result["paper_values_configured"] = configured
    if configured:
        latex_result["ok"] = bool(latex_result.get("ok")) and report.ok
    return latex_result
