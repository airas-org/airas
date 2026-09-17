from __future__ import annotations

from pathlib import Path
from typing import Any, Literal

from airas.core.research_paths import COMPARISON_KEY, RESULTS_DIR
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
    ClaimStatus,
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
) -> list[str]:
    """At the prereg stage nothing measured exists, so nothing realized may;
    afterwards every recorded result is the run outputs' copy, every params
    declaration is what executed, and no outputs lack a declared run."""
    if stage == "prereg":
        realized = [run.run_id for run in record.run_index().values() if run.results]
        realized += [c.id for _, c in record.active_claims() if c.verified or c.verdict]
        if realized:
            return [
                "record.json holds results but no run outputs exist "
                f"({', '.join(sorted(set(realized)))})"
            ]
        return []
    manifest = load_provenance_manifest(root)
    problems: list[str] = []
    for _, claim in record.active_claims():
        for _, run in claim.runs():
            if isinstance(claim, SeyvalClaim):
                problems += _params_problems(run, manifest)
            problems += _result_problems(root, claim, run, metrics_data, manifest)
    declared_runs = set(record.run_index())
    undeclared = sorted(
        d for d in metrics_data if d != COMPARISON_KEY and d not in declared_runs
    )
    if undeclared:
        problems.append(
            "results directories no declared run accounts for: " + ", ".join(undeclared)
        )
    drifted = _verified_problems(
        record, compute_claim_statuses(record, reported_run_ids)
    )
    if drifted:
        problems.append(
            "claims stored as verified, or with a verdict, that the recomputation finds otherwise "
            f"({', '.join(drifted)})"
        )
    return problems


def _params_problems(run: AnyRun, manifest: RunProvenanceManifest | None) -> list[str]:
    problems: list[str] = []
    declared = manifest.dirs.get(run.run_id) if manifest else None
    if declared is None or not run.params:
        return problems
    resolved = declared.parameters or {
        k.lower(): v for k, v in declared.overrides.items()
    }
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


def _result_problems(
    root: Path,
    claim: ClaimDeclaration,
    run: AnyRun,
    metrics_data: dict[str, Any],
    manifest: RunProvenanceManifest | None,
) -> list[str]:
    result = run.latest_result()
    if result is None:
        return []
    rid = run.run_id
    if not isinstance(result, SeyvalResult):
        # The verifier's report is the source; the entry must be its copy.
        expected = derive_result(root, claim, run, metrics_data, manifest)
        if expected is None or expected.model_dump() != result.model_dump():
            return [
                f"run '{rid}': the result differs from the {claim.verifier.kind} "
                "report in the results directory"
            ]
        return []

    problems: list[str] = []
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

    expected_inputs = load_eval_inputs_ref(root, rid)
    if (result.eval_inputs is None) != (expected_inputs is None) or (
        result.eval_inputs is not None
        and expected_inputs is not None
        and result.eval_inputs.model_dump() != expected_inputs.model_dump()
    ):
        problems.append(
            f"run '{rid}': the result's eval_inputs hash does not match "
            "the eval_inputs file in the results directory"
        )

    expected_eval = load_eval_report(root, rid)
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


def _verified_problems(
    record: ResearchRecord, statuses: list[ClaimStatus]
) -> list[str]:
    """Claims stored as verified, or with a verdict, that the recomputation finds otherwise.

    A stored true is a fact the history must still bear out. The reverse —
    recomputed true, stored false — is not a problem: update_record has
    simply not run since the procedure completed.
    """
    recomputed = {s.id: s for s in statuses}
    drifted = []
    for _, claim in record.active_claims():
        status = recomputed.get(claim.id)
        if claim.verified and not (status and status.verified):
            drifted.append(claim.id)
        elif claim.verdict and not (status and status.verdict == claim.verdict):
            drifted.append(claim.id)
    return drifted
