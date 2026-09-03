from __future__ import annotations

import re
from math import isclose
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
from airas.usecases.publication.paper_values.charts import (
    chart_result_dirs,
    verify_charts,
)
from airas.usecases.publication.paper_values.compute import (
    COMPARISON_KEY,
    RESULTS_DIR,
    compute_claim_values,
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
    active,
    load_record,
    orphan_runs,
    override_problems,
    record_consistency_problems,
    ref_run_id,
    run_index,
    selected_execution,
)
from airas.usecases.publication.paper_values.tables import (
    TABLES_DIR_NAME,
    render_table_tex,
    table_result_dirs,
    table_tex_relpath,
)
from airas.usecases.verification.record_history import (
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


def execution_problems(
    root: Path,
    record: ResearchRecord,
    metrics_data: dict[str, Any],
    manifest: RunProvenanceManifest | None,
) -> list[str]:
    """Is every value the record holds about an execution re-derivable?

    An execution entry is a set of copies: of the manifest (which run, which
    commit, which parameters), of the metrics file, of the inputs' hash, of
    the evaluator's report. Each copy is compared with what it claims to
    copy. Without this, an execution appended by hand could carry numbers
    that no file, no manifest and no platform record ever produced — and
    pass, because containment allows appends and the claim recomputation
    reads the files rather than the record.

    The sources themselves are anchored elsewhere: the manifest and the
    files to Seyval, the commit to git. This check only asks that the
    record agree with them.
    """
    problems: list[str] = []
    for run in run_index(record).values():
        execution = selected_execution(run)
        if execution is None:
            continue
        rid = run.run_id

        declared = manifest.dirs.get(rid) if manifest else None
        if declared is not None:
            if execution.execution_id != declared.execution_id:
                problems.append(
                    f"run '{rid}': the record's execution_id "
                    f"{execution.execution_id!r} is not the manifest's "
                    f"{declared.execution_id!r}"
                )
            if execution.commit != declared.commit_hash:
                problems.append(
                    f"run '{rid}': the record's commit {execution.commit!r} is "
                    f"not the manifest's {declared.commit_hash!r}"
                )
            if dict(execution.overrides) != dict(declared.overrides):
                problems.append(
                    f"run '{rid}': the record's overrides differ from the manifest's"
                )
            if dict(execution.parameters) != dict(declared.parameters):
                problems.append(
                    f"run '{rid}': the record's parameters differ from the manifest's"
                )
        elif execution.execution_id or execution.commit:
            problems.append(
                f"run '{rid}': the record names an execution but no readable "
                f"{PROVENANCE_MANIFEST_PATH} entry declares one for this directory"
            )

        if rid in metrics_data and execution.metrics != metrics_data[rid]:
            problems.append(
                f"run '{rid}': the record's copy of metrics differs from "
                f"{RESULTS_DIR}/{rid}/metrics.json"
            )

        expected_inputs = eval_inputs_ref(root, rid)
        stored_inputs = execution.inputs
        if (stored_inputs is None) != (expected_inputs is None) or (
            stored_inputs is not None
            and expected_inputs is not None
            and stored_inputs.model_dump() != expected_inputs.model_dump()
        ):
            problems.append(
                f"run '{rid}': the record's inputs hash does not match the "
                "eval_inputs file in the results directory"
            )

        expected_eval = eval_report(root, rid)
        stored_eval = execution.evaluation
        if (stored_eval is None) != (expected_eval is None) or (
            stored_eval is not None
            and expected_eval is not None
            and stored_eval.model_dump() != expected_eval.model_dump()
        ):
            problems.append(
                f"run '{rid}': the record's evaluation differs from the "
                "evaluator's report in the results directory"
            )

        # The evaluator says which inputs it computed from. That must be the
        # inputs the record hashed, or the metrics and the inputs describe
        # two different experiments.
        if (
            stored_eval is not None
            and stored_inputs is not None
            and stored_eval.inputs_sha256
            and stored_eval.inputs_sha256 != stored_inputs.sha256
        ):
            problems.append(
                f"run '{rid}': the evaluator reports inputs "
                f"{stored_eval.inputs_sha256[:12]} but the record's inputs "
                f"hash is {stored_inputs.sha256[:12]}"
            )
    return problems


def claim_evaluation_drift(
    record: ResearchRecord, claims: list[ClaimStatus]
) -> list[str]:
    """Claim ids whose stored evaluation disagrees with the recomputation.

    The value is compared, not only the two verdicts: a metric can be edited
    in a way that moves the number the paper prints while leaving the
    criterion satisfied and the order proof intact, and comparing verdicts
    alone would call that record consistent.
    """
    stored = {
        c.id: c.evaluations[-1]
        for c in active(record.hypothesis.claims, "id")
        if c.evaluations
    }
    return [
        s.id
        for s in claims
        if s.id not in stored
        or stored[s.id].verified != s.verified
        or stored[s.id].criterion_met != s.criterion_met
        or stored[s.id].display != (s.display or "")
        or stored[s.id].used_executions != s.used_executions
        or (
            s.value is not None
            and not isclose(stored[s.id].value, s.value, rel_tol=1e-9)
        )
    ]


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
            record = ResearchRecord.model_validate_json(
                record_file.read_text(encoding="utf-8")
            )
        except ValidationError as e:
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
    append_only: Literal["ok", "violated", "unavailable"] = "unavailable"
    append_only_problems: list[str] = []
    record_commits: list[str] = []
    claims: list[ClaimStatus] = []
    claim_status_match = True
    undeclared_result_dirs: list[str] = []

    orphans: list[str] = []
    refuted: list[str] = []

    if record is not None:
        mismatches.extend(record_consistency_problems(record))
        mismatches.extend(override_problems(record))
        if metrics_data:
            mismatches.extend(
                execution_problems(
                    root, record, metrics_data, load_provenance_manifest(root)
                )
            )
        orphans = orphan_runs(record)
        append_only, append_only_problems, record_commits = record_append_only_status(
            root, record
        )

        if stage == "prereg":
            # Nothing measured yet, so nothing realized may exist: a
            # values.tex carried over without runs would put unverifiable
            # numbers in the PDF.
            values_match = True
            values_tex_match = True
            realized = [c.id for c in record.hypothesis.claims if c.evaluations] + [
                run.run_id for run in run_index(record).values() if run.executions
            ]
            if realized:
                mismatches.append(
                    "record.json holds realized results but no run outputs "
                    f"exist ({', '.join(sorted(set(realized)))})"
                )
            if values_tex_path.is_file():
                mismatches.append(
                    f"{VALUES_TEX_FILENAME} exists but no run outputs exist"
                )
            if (latex_dir / TABLES_DIR_NAME).is_dir():
                mismatches.append(f"{TABLES_DIR_NAME}/ exists but no run outputs exist")
            claims = compute_claim_status(root, record, None, set())
        else:
            assert metrics_data is not None
            try:
                claim_values = compute_claim_values(record, metrics_data)
            except ValueError as e:
                mismatches.append(str(e))
                claim_values = {}
            else:
                paper_values, undefined_keys = resolve_paper_values(
                    record, metrics_data, used_keys
                )
                values_match = True
                if values_tex_path.is_file():
                    values_tex_match = values_tex_path.read_text(
                        encoding="utf-8"
                    ) == render_values_tex(
                        paper_values,
                        record.link_base,
                        record_commits[-1] if record_commits else None,
                    )
                    if not values_tex_match:
                        mismatches.append(
                            f"{VALUES_TEX_FILENAME} differs from its "
                            "regeneration (manual edit?)"
                        )
                mismatches.extend(
                    _verify_tables(
                        latex_dir, active(record.tables, "key"), metrics_data
                    )
                )
                mismatches.extend(verify_charts(record, str(root), metrics_data))

            declared_runs = set(run_index(record))
            undeclared_result_dirs = sorted(
                d
                for d in metrics_data
                if d != COMPARISON_KEY and d not in declared_runs
            )
            manifest = load_provenance_manifest(root)
            claims = compute_claim_status(
                root, record, manifest, set(metrics_data), claim_values
            )

            drifted = claim_evaluation_drift(record, claims)
            claim_status_match = not drifted
            if drifted:
                mismatches.append(
                    "stored claim evaluations differ from their recomputation "
                    f"({', '.join(drifted)}) — run update_record again"
                )
            refuted = [s.id for s in claims if s.criterion_met is False]

    return PaperValuesVerificationReport(
        ok=(
            not missing_files
            and values_match
            and values_tex_match
            and not undefined_keys
            and not mismatches
            and append_only != "violated"
            and claim_status_match
            and not undeclared_result_dirs
        ),
        stage=stage,
        values_match=values_match,
        values_tex_match=values_tex_match,
        mismatches=mismatches,
        missing_files=missing_files,
        undefined_keys=undefined_keys,
        append_only=append_only,
        append_only_problems=append_only_problems,
        record_commits=record_commits,
        claims=claims,
        claim_status_match=claim_status_match,
        undeclared_result_dirs=undeclared_result_dirs,
        refuted_claims=refuted,
        orphan_runs=orphans,
        unverified_claims=[s.id for s in claims if not s.verified],
        unverified=unverified,
    )


def referenced_result_dirs(local_repo_path: str) -> set[str]:
    """The results directories the paper draws data or claim support from."""
    try:
        record = load_record(local_repo_path)
        metrics_data = load_metrics_data(local_repo_path)
    except (ValidationError, ValueError):
        return set()

    dirs = used_result_dirs(record, metrics_data)
    dirs |= table_result_dirs(active(record.tables, "key"), metrics_data)
    dirs |= chart_result_dirs(record, metrics_data)
    dirs |= {
        run_id
        for claim in active(record.hypothesis.claims, "id")
        for ref in claim.target.refs
        if (run_id := ref_run_id(ref)) in metrics_data
    }
    return dirs


def apply_provenance_result(
    report: PaperValuesVerificationReport, provenance: ProvenanceCheckResult
) -> PaperValuesVerificationReport:
    # A mismatch means the local metrics are not backed by any completed
    # run in the platform's storage; "unavailable" is surfaced but only
    # fails in CI, which requires the guarantee.
    report.provenance = provenance
    if provenance.status == "mismatch":
        report.ok = False
        report.mismatches.append(
            f"{provenance.source}: local metrics are not backed by stored "
            "run outputs — " + (provenance.detail or "see provenance.checks")
        )
    return report


def paper_values_configured(report: PaperValuesVerificationReport) -> bool:
    """Whether the paper opted into the record system (record.json exists)."""
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
