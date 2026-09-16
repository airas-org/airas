"""Deriving each run's result and each claim's verdict from the outputs.

The write path and the gate share this module: rule 2 of the integrity
model is that anything machine-derived must equal its re-derivation at
verification time, which only holds if both sides run the same code.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from pydantic import BaseModel

from airas.core.types.research_record import (
    AnyRun,
    ClaimDeclaration,
    LeanClaim,
    LeanResult,
    LeanRun,
    LlmJudgeClaim,
    LlmJudgeResult,
    ResearchRecord,
    RunResult,
    SeyvalClaim,
    SeyvalResult,
    Verdict,
)
from airas.core.types.run_provenance import RunProvenanceManifest
from airas.research_record.read_run_outputs import (
    _read_json,
    _verifier_report_path,
    load_eval_inputs_ref,
    load_eval_report,
    runs_with_reports,
)


class ClaimStatus(BaseModel):
    id: str
    # Every run under the claim has its verifier's report in the results
    # directory: the data the claim rests on is in. Whether the claim was
    # declared before those runs executed is not modelled yet (TODO).
    verified: bool
    verdict: Verdict | None = None


def update_record_with_results(
    root: Path,
    record: ResearchRecord,
    metrics_data: dict[str, Any],
    manifest: RunProvenanceManifest | None,
) -> tuple[list[ClaimStatus], int]:
    # Results are appended, never replaced: running again adds an entry.
    # verified and verdict are set once and never back; a later disagreement
    # is a verification failure to report, not a value to overwrite.
    appended = 0
    for _, claim in record.active_claims():
        for _, run in claim.runs():
            result = derive_result(root, claim, run, metrics_data, manifest)
            if result is None:
                continue
            latest = run.latest_result()
            if latest is None or latest.model_dump() != result.model_dump():
                run.results.append(result)
                appended += 1

    statuses = compute_claim_statuses(record, runs_with_reports(root, record))
    claims = record.claim_index()
    for status in statuses:
        claim = claims[status.id]
        if status.verified:
            claim.verified = True
        if status.verdict and claim.verdict is None:
            claim.verdict = status.verdict
    return statuses, appended


def compute_claim_statuses(
    record: ResearchRecord, present_run_ids: set[str]
) -> list[ClaimStatus]:
    statuses: list[ClaimStatus] = []
    for _, claim in record.active_claims():
        runs = [run for _, run in claim.runs()]
        verified = bool(runs) and all(run.run_id in present_run_ids for run in runs)
        results = {
            run.run_id: r for run in runs if (r := run.latest_result()) is not None
        }
        statuses.append(
            ClaimStatus(
                id=claim.id,
                verified=verified,
                verdict=(
                    _claim_verdict(claim, results)
                    if verified and len(results) == len(runs)
                    else None
                ),
            )
        )
    return statuses


def derive_result(
    root: Path,
    claim: ClaimDeclaration,
    run: AnyRun,
    metrics_data: dict[str, Any],
    manifest: RunProvenanceManifest | None,
) -> RunResult | None:
    if isinstance(claim, SeyvalClaim):
        # A seyval result is the platform's fact: without a manifest entry
        # there is nothing to copy.
        declared = manifest.dirs.get(run.run_id) if manifest else None
        if run.run_id not in metrics_data or declared is None:
            return None
        return SeyvalResult(
            id=declared.execution_id,
            commit=declared.commit_hash,
            eval_inputs=load_eval_inputs_ref(root, run.run_id),
            eval_report=load_eval_report(root, run.run_id),
            metrics=metrics_data[run.run_id],
        )
    payload = _read_json(_verifier_report_path(root, claim.verifier.kind, run.run_id))
    if not isinstance(payload, dict):
        return None

    declared = manifest.dirs.get(run.run_id) if manifest else None
    try:
        if isinstance(claim, LeanClaim):
            return LeanResult(
                id=declared.execution_id if declared else "",
                commit=payload.get("commit"),
                toolchain=payload.get("toolchain", ""),
                mathlib_rev=payload.get("mathlib_rev", ""),
                statement=payload.get("statement", ""),
                # Stored only as the tool wrote it: a coerced 1 or "false"
                # would look like a verdict the tool never gave.
                statement_matches=(
                    payload["statement_matches"]
                    if isinstance(payload.get("statement_matches"), bool)
                    else None
                ),
                axioms=payload.get("axioms", []),
                errors=_lean_errors(claim, run, payload),
                warnings=payload.get("warnings", []),
            )
        votes = payload.get("votes", {})
        return LlmJudgeResult(
            id=payload.get("id", ""),
            commit=payload.get("commit"),
            inputs_sha256=payload["inputs_sha256"],
            verdict=payload["verdict"],
            errors=payload.get("errors", []),
            warnings=[f"votes split {votes}"] if len(votes) > 1 else [],
        )
    except (KeyError, ValueError):
        return None


# ------------------------------------------ what the verifier concluded

_SORRY_AXIOM = "sorryAx"


def _claim_verdict(
    claim: ClaimDeclaration, results: dict[str, RunResult]
) -> Verdict | None:
    if any(r.errors for r in results.values() if not isinstance(r, SeyvalResult)):
        return "inconclusive"
    if isinstance(claim, LeanClaim):
        # Lean cannot refute: a proof that did not go through shows nothing.
        return "supported"
    if isinstance(claim, LlmJudgeClaim):
        verdicts = {
            r.verdict for r in results.values() if isinstance(r, LlmJudgeResult)
        }
        if verdicts == {"supported"}:
            return "supported"
        return "refuted" if "refuted" in verdicts else "inconclusive"
    metrics = {
        rid: r.metrics for rid, r in results.items() if isinstance(r, SeyvalResult)
    }
    try:
        difference = claim.criterion.observed(metrics)
    except (KeyError, ValueError):
        return "inconclusive"  # the criterion names a value the run did not produce
    return "supported" if claim.criterion.holds(difference) else "refuted"


def _lean_errors(claim: LeanClaim, run: LeanRun, payload: dict[str, Any]) -> list[str]:
    errors = list(payload.get("errors", []))
    if errors:
        return errors
    # The report names what it built; each must be what the record declared,
    # or the statement below was checked against the wrong thing.
    for key, wanted in (
        ("module", run.params.module),
        ("decl", run.params.decl),
        ("toolchain", claim.verifier.toolchain),
        ("mathlib_rev", claim.verifier.mathlib_rev),
    ):
        built_value = payload.get(key)
        if wanted and built_value != wanted:
            errors.append(f"{key} differs from the declaration: built {built_value!r}")
    if errors:
        return errors
    # The report tool compares the declared statement with the built type as
    # Lean terms; a report without that verdict has not checked the claim's
    # statement at all, so it proves nothing about it.
    match payload.get("statement_matches"):
        case True:
            pass
        case False:
            errors.append(
                "statement differs from the declaration: built "
                f"'{payload.get('statement', '')}'"
            )
        case None:
            errors.append("the report did not compare the declared statement")
        case other:
            errors.append(f"statement_matches must be true or false, not {other!r}")
    axioms = set(payload.get("axioms", []))
    if _SORRY_AXIOM in axioms:
        errors.append("the proof uses sorry")
    foreign = sorted(axioms - set(claim.verifier.allowed_axioms) - {_SORRY_AXIOM})
    if foreign:
        errors.append(f"depends on axioms outside allowed_axioms: {', '.join(foreign)}")
    return errors
