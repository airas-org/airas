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
    ClaimEvaluation,
    EvalReport,
    Execution,
    InputRef,
    ResearchRecord,
)
from airas.core.types.run_provenance import RunProvenanceManifest
from airas.usecases.publication.paper_values.compute import compute_claim_values
from airas.usecases.publication.paper_values.record import active, run_index
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
    """Append what the runs produced, and evaluate every claim against it.

    Executions are appended rather than replaced: running the same
    configuration again adds an entry and the earlier numbers stay, so "we
    ran it three times" is in the record and which execution a number came
    from is recorded with it.

    Returns the recomputed claim statuses and how many executions were added.
    """
    appended = 0
    for run in run_index(record).values():
        if run.run_id not in metrics_data:
            continue
        declared = manifest.dirs.get(run.run_id) if manifest else None
        execution = Execution(
            execution_id=declared.execution_id if declared else None,
            commit=declared.commit_hash if declared else None,
            # Both from the platform's record of the dispatch, which the
            # experiment code cannot write — unlike the metrics below.
            overrides=dict(declared.overrides) if declared else {},
            parameters=dict(declared.parameters) if declared else {},
            inputs=eval_inputs_ref(root, run.run_id),
            evaluation=eval_report(root, run.run_id),
            metrics=metrics_data[run.run_id],
        )
        latest = run.executions[-1] if run.executions else None
        if latest is None or latest.model_dump() != execution.model_dump():
            run.executions.append(execution)
            appended += 1

    claim_values = compute_claim_values(record, metrics_data)
    statuses = compute_claim_status(
        root, record, manifest, set(metrics_data), claim_values
    )

    claims_by_id = {c.id: c for c in active(record.hypothesis.claims, "id")}
    for status in statuses:
        claim = claims_by_id.get(status.id)
        if claim is None or status.value is None:
            continue
        claim.evaluations.append(
            ClaimEvaluation(
                used_executions=status.used_executions,
                value=status.value,
                display=status.display or "",
                verified=status.verified,
                criterion_met=bool(status.criterion_met),
                detail="; ".join(c.detail for c in status.checks if c.detail),
            )
        )
    return statuses, appended
