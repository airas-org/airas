"""Turn run outputs into record entries.

Extracted from the MCP tool so the realization the paper depends on is the
same code a test can call: while it lived inside the tool, a test could only
re-implement it, and a re-implementation that drifts proves nothing about
what actually runs.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from airas.core.research_paths import RESULTS_DIR
from airas.core.types.paper_values import ClaimStatus
from airas.core.types.research_record import (
    EvalReport,
    InputRef,
    ResearchRecord,
    RunResult,
)
from airas.core.types.run_provenance import RunProvenanceManifest
from airas.usecases.publication.paper_values.record import claim_index, run_index
from airas.usecases.verification.record_history import compute_claim_status

EVAL_INPUTS_DIRNAME = "eval_inputs"
EVALUATION_DIRNAME = "evaluation"


def eval_inputs_ref(root: Path, run_id: str) -> InputRef | None:
    """Hash the raw predictions an execution produced.

    These are the re-derivation anchor: the metrics can be recomputed from
    them by the pinned evaluation layer, so the record pins the input and not
    only the conclusion drawn from it.
    """
    inputs_dir = root / RESULTS_DIR / run_id / EVAL_INPUTS_DIRNAME
    if not inputs_dir.is_dir():
        return None
    for path in sorted(inputs_dir.glob("*.json")):
        return InputRef(
            path=str(path.relative_to(root)),
            sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
        )
    return None


def eval_report(root: Path, run_id: str) -> EvalReport | None:
    """Carry the evaluation layer's verdict into the record.

    `skipped` comes along because a metric that could not be computed is a
    result too, and the suite signature with the resolved versions is what
    makes the numbers reproducible as (inputs, evaluator) -> metrics.
    """
    eval_dir = root / RESULTS_DIR / run_id / EVALUATION_DIRNAME
    if not eval_dir.is_dir():
        return None
    for path in sorted(eval_dir.glob("*.json")):
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return None
        provenance = payload.get("provenance") or {}
        return EvalReport(
            task_type=payload.get("task_type", path.stem),
            task_signature=provenance.get("task_signature"),
            inputs_sha256=provenance.get("inputs_sha256"),
            versions={
                key: str(value)
                for key, value in (provenance.get("versions") or {}).items()
            },
            metrics={
                key: float(value)
                for key, value in (payload.get("metrics") or {}).items()
                if isinstance(value, (int, float)) and not isinstance(value, bool)
            },
            curves=payload.get("curves") or {},
            inputs_summary=payload.get("inputs_summary") or {},
            skipped=payload.get("skipped") or {},
        )
    return None


def realize_record(
    root: Path,
    record: ResearchRecord,
    metrics_data: dict[str, Any],
    manifest: RunProvenanceManifest | None,
) -> tuple[list[ClaimStatus], int]:
    """Append what the runs produced, and mark the claims all of whose runs have results.

    Results are appended rather than replaced: running the same configuration
    again adds an entry and the earlier one stays, so "we ran it three times"
    is in the record. Only a run the manifest declares an execution for is
    recorded — a result entry is the platform's fact, and without the
    manifest there is no platform fact to copy.

    `verified` is set to true, once, when every run under a claim has
    results. It is never set back: a later disagreement is a verification
    failure to report, not a value to overwrite.

    Returns the recomputed claim statuses and how many results were added.
    """
    appended = 0
    for run in run_index(record).values():
        if run.run_id not in metrics_data:
            continue
        declared = manifest.dirs.get(run.run_id) if manifest else None
        if declared is None:
            continue
        result = RunResult(
            id=declared.execution_id,
            commit=declared.commit_hash,
            eval_inputs=eval_inputs_ref(root, run.run_id),
            eval_report=eval_report(root, run.run_id),
            metrics=metrics_data[run.run_id],
        )
        latest = run.results[-1] if run.results else None
        if latest is None or latest.model_dump() != result.model_dump():
            run.results.append(result)
            appended += 1

    statuses = compute_claim_status(record, set(metrics_data))
    claims = claim_index(record)
    for status in statuses:
        claim = claims.get(status.id)
        if claim is not None and status.verified:
            claim.verified = True
    return statuses, appended
