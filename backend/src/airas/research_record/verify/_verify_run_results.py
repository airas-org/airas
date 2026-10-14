from __future__ import annotations

from pathlib import Path
from typing import Any, Literal

from airas.core.research_paths import COMPARISON_KEY, RECORD_PATH, RESULTS_DIR
from airas.core.types.record_verification import RecordVerification
from airas.core.types.research_record import (
    AnyRun,
    ClaimDeclaration,
    ResearchRecord,
    SeyvalClaim,
    SeyvalResult,
)
from airas.core.types.run_provenance import (
    PROVENANCE_MANIFEST_PATH,
    RunProvenanceManifest,
)
from airas.research_record.read.derive_results import (
    compute_claim_statuses,
    derive_result,
)
from airas.research_record.read.read_run_outputs import (
    load_eval_inputs_ref,
    load_eval_report,
    load_provenance_manifest,
)


def verify_run_results(
    root: Path,
    record: ResearchRecord,
    metrics_data: dict[str, Any],
    reported_run_ids: set[str],
    stage: Literal["prereg", "results"],
    verification: RecordVerification,
) -> None:
    """At the prereg stage nothing measured exists, so nothing realized may;
    afterwards every recorded result is the run outputs' copy, every params
    declaration is what executed, and no outputs lack a declared run."""
    if stage == "prereg":
        realized = [run.run_id for run in record.run_index().values() if run.results]
        realized += [c.id for _, c in record.latest_claims() if c.verified or c.verdict]
        if realized:
            verification.append_declaration_status(
                RECORD_PATH,
                "record.json holds results but no run outputs exist "
                f"({', '.join(sorted(set(realized)))})",
                "mismatch",
            )
        return
    manifest = load_provenance_manifest(root)
    for hypothesis, claim, design, run in record.latest_runs():
        run_path = (
            f"hypotheses[{hypothesis.id}]/claims[{claim.id}]/designs[{design.id}]"
            f"/runs[{run.run_id}]"
        )
        if isinstance(claim, SeyvalClaim):
            # 上流引数と同じキーは observed との照合（_verify_run_observations）が書く
            integration = getattr(design, "repository_integration", None)
            upstream = set(integration.arguments) if integration else set()
            _append_params_statuses(run, upstream, manifest, run_path, verification)
        _append_result_statuses(
            root, claim, run, metrics_data, manifest, run_path, verification
        )
    declared_runs = set(record.run_index())
    undeclared = sorted(
        d for d in metrics_data if d != COMPARISON_KEY and d not in declared_runs
    )
    if undeclared:
        verification.append_declaration_status(
            RESULTS_DIR,
            "results directories no declared run accounts for: "
            + ", ".join(undeclared),
            "mismatch",
        )
    _append_verified_statuses(record, reported_run_ids, verification)


def _append_params_statuses(
    run: AnyRun,
    upstream: set[str],
    manifest: RunProvenanceManifest | None,
    run_path: str,
    verification: RecordVerification,
) -> None:
    declared = manifest.dirs.get(run.run_id) if manifest else None
    params = {k: v for k, v in run.params.items() if k not in upstream}
    if not params:
        return

    if declared is None:
        for key in params:
            verification.append_declaration_status(
                f"{run_path}/params/{key}",
                f"no {PROVENANCE_MANIFEST_PATH} entry for the run",
                "unverified",
                evidence_path=PROVENANCE_MANIFEST_PATH,
            )
        return

    resolved = declared.parameters or {
        k.lower(): v for k, v in declared.overrides.items()
    }
    complete = bool(declared.parameters)
    source = "parameters" if complete else "overrides"
    for key, wanted in params.items():
        path = f"{run_path}/params/{key}"
        if key not in resolved:
            if complete:
                verification.append_declaration_status(
                    path,
                    f"run '{run.run_id}': declared '{key}={wanted}' but "
                    "the execution resolved no such parameter",
                    "mismatch",
                )
            else:
                verification.append_declaration_status(
                    path,
                    f"{PROVENANCE_MANIFEST_PATH} holds only overrides, none for this key",
                    "unverified",
                )
            continue

        same = str(resolved[key]) == str(wanted)
        verification.append_declaration_status(
            path,
            f"{PROVENANCE_MANIFEST_PATH} {source}: {key}={resolved[key]}"
            if same
            else f"run '{run.run_id}': declared '{key}={wanted}' but "
            f"executed '{key}={resolved[key]}'",
            "verified" if same else "mismatch",
        )


def _append_result_statuses(
    root: Path,
    claim: ClaimDeclaration,
    run: AnyRun,
    metrics_data: dict[str, Any],
    manifest: RunProvenanceManifest | None,
    run_path: str,
    verification: RecordVerification,
) -> None:
    result = run.latest_result()
    if result is None:
        return
    rid = run.run_id
    result_path = f"{run_path}/results[{result.id}]"
    if not isinstance(result, SeyvalResult):
        # The verifier's report is the source; the entry must be its copy.
        expected = derive_result(root, claim, run, metrics_data, manifest)
        same = expected is not None and expected.model_dump() == result.model_dump()
        verification.append_declaration_status(
            result_path,
            f"the {claim.verifier.kind} report in {RESULTS_DIR}/{rid}/"
            if same
            else f"run '{rid}': the result differs from the {claim.verifier.kind} "
            "report in the results directory",
            "verified" if same else "mismatch",
            evidence_path=f"{RESULTS_DIR}/{rid}/",
        )
        return

    declared = manifest.dirs.get(rid) if manifest else None
    if declared is None:
        verification.append_declaration_status(
            result_path,
            f"run '{rid}': the record holds a result but no readable "
            f"{PROVENANCE_MANIFEST_PATH} entry declares an execution for "
            "this directory",
            "mismatch",
            evidence_path=PROVENANCE_MANIFEST_PATH,
        )
    else:
        same_id = result.id == declared.execution_id
        verification.append_declaration_status(
            f"{result_path}/id",
            f"{PROVENANCE_MANIFEST_PATH} execution {declared.execution_id!r}"
            if same_id
            else f"run '{rid}': the result's id {result.id!r} is not the "
            f"manifest's execution {declared.execution_id!r}",
            "verified" if same_id else "mismatch",
            evidence_path=PROVENANCE_MANIFEST_PATH,
        )
        same_commit = result.commit == declared.commit_hash
        verification.append_declaration_status(
            f"{result_path}/commit",
            f"{PROVENANCE_MANIFEST_PATH} commit {declared.commit_hash!r}"
            if same_commit
            else f"run '{rid}': the result's commit {result.commit!r} is "
            f"not the manifest's {declared.commit_hash!r}",
            "verified" if same_commit else "mismatch",
            evidence_path=PROVENANCE_MANIFEST_PATH,
        )

    if rid in metrics_data:
        same_metrics = result.metrics == metrics_data[rid]
        verification.append_declaration_status(
            f"{result_path}/metrics",
            f"{RESULTS_DIR}/{rid}/metrics.json"
            if same_metrics
            else f"run '{rid}': the result's metrics differ from "
            f"{RESULTS_DIR}/{rid}/metrics.json",
            "verified" if same_metrics else "mismatch",
            evidence_path=f"{RESULTS_DIR}/{rid}/metrics.json",
        )

    expected_inputs = load_eval_inputs_ref(root, rid)
    if result.eval_inputs is not None or expected_inputs is not None:
        same_inputs = (
            result.eval_inputs is not None
            and expected_inputs is not None
            and result.eval_inputs.model_dump() == expected_inputs.model_dump()
        )
        verification.append_declaration_status(
            f"{result_path}/eval_inputs",
            f"sha256 of the eval_inputs file in {RESULTS_DIR}/{rid}/"
            if same_inputs
            else f"run '{rid}': the result's eval_inputs hash does not match "
            "the eval_inputs file in the results directory",
            "verified" if same_inputs else "mismatch",
            evidence_path=f"{RESULTS_DIR}/{rid}/",
        )

    expected_eval = load_eval_report(root, rid)
    if result.eval_report is not None or expected_eval is not None:
        same_eval = (
            result.eval_report is not None
            and expected_eval is not None
            and result.eval_report.model_dump() == expected_eval.model_dump()
        )
        verification.append_declaration_status(
            f"{result_path}/eval_report",
            f"the evaluator's report in {RESULTS_DIR}/{rid}/"
            if same_eval
            else f"run '{rid}': the result's eval_report differs from the "
            "evaluator's report in the results directory",
            "verified" if same_eval else "mismatch",
            evidence_path=f"{RESULTS_DIR}/{rid}/",
        )

    # The evaluator's own `inputs_sha256` is deliberately not compared
    # with `eval_inputs.sha256`. airas-eval hashes the *parsed* payload
    # in a canonical JSON form (sorted keys, no whitespace, its own type
    # coercion), while the record hashes the file's bytes, so the two
    # digests differ for every honest run. The evaluator's digest is
    # still carried verbatim — it names what the evaluator scored in the
    # evaluator's own terms — and the file hash is what the provenance
    # step holds against the platform's stored bytes.


def _append_verified_statuses(
    record: ResearchRecord, reported_run_ids: set[str], verification: RecordVerification
) -> None:
    """A stored true is a fact the history must still bear out. The reverse —
    recomputed true, stored false — is not a problem: update_record has
    simply not run since the procedure completed."""
    recomputed = {s.id: s for s in compute_claim_statuses(record, reported_run_ids)}
    for hypothesis, claim in record.latest_claims():
        claim_path = f"hypotheses[{hypothesis.id}]/claims[{claim.id}]"
        status = recomputed.get(claim.id)
        if claim.verified:
            held = bool(status and status.verified)
            verification.append_declaration_status(
                f"{claim_path}/verified",
                "recomputed from the runs' outputs"
                if held
                else f"claim {claim.id}: stored as verified, which the recomputation "
                "from the run outputs finds otherwise",
                "verified" if held else "mismatch",
                evidence_path=RESULTS_DIR,
            )
            if not held:
                continue
        if claim.verdict:
            held = bool(status and status.verdict == claim.verdict)
            verification.append_declaration_status(
                f"{claim_path}/verdict",
                f"criterion applied to the runs' metrics: {status.verdict if status else None}"
                if held
                else f"claim {claim.id}: stored with a verdict {claim.verdict}, which the "
                f"recomputation finds {status.verdict if status else None}",
                "verified" if held else "mismatch",
                evidence_path=RESULTS_DIR,
            )
