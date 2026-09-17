"""The record gate: is record.json what was declared, whole, and backed by
the run outputs? Composes the checks in the `_verify_*` modules."""

from __future__ import annotations

import asyncio
from pathlib import Path
from typing import Literal

from pydantic import ValidationError

from airas.core.research_paths import RECORD_PATH
from airas.core.types.record_verification import RecordVerification
from airas.core.types.research_record import ResearchRecord
from airas.infra.run_output_store import default_store
from airas.research_record.read.load_record import load_record
from airas.research_record.read.read_run_outputs import (
    load_metrics_data,
    runs_with_reports,
)
from airas.research_record.verify._verify_quoted_passages import verify_quoted_passages
from airas.research_record.verify._verify_record_declarations import (
    verify_record_declarations,
)
from airas.research_record.verify._verify_record_history import verify_record_history
from airas.research_record.verify._verify_results_against_store import (
    StoreFactory,
    _ProvenanceCheckResult,
    provenance_problems,
    provenance_scope,
    verify_results_against_store,
)
from airas.research_record.verify._verify_run_results import verify_run_results


def verify_record_offline(root: Path, record: ResearchRecord) -> list[str]:
    """What holds of a record on the working tree alone, with no git history
    and no platform: its declarations are consistent and its sources are
    snapshotted with their quotes. The writers run this before committing."""
    return verify_record_declarations(record) + verify_quoted_passages(root, record)


async def verify_record(
    local_path: str,
    *,
    check_provenance: bool = True,
    require_provenance: bool = True,
    require_history: bool = True,
    require_record: bool = True,
    store_factory: StoreFactory = default_store,
) -> RecordVerification:
    root = Path(local_path).expanduser().resolve()
    if not (root / RECORD_PATH).is_file():
        # An AIRAS repository ships record.json (empty at first), so its
        # absence is not an initial state — it was deleted, taking the
        # declarations the gate reads with it. The gate requires it;
        # verify_paper's preview (require_record=False) tolerates a paper that
        # opts out of the record system.
        problems = (
            [
                "record.json is missing: every AIRAS repository ships one "
                "(empty at first), so its absence means it was deleted"
            ]
            if require_record
            else []
        )
        return RecordVerification(ok=not problems, stage="prereg", problems=problems)

    try:
        record = load_record(str(root))
    except (ValidationError, ValueError) as e:
        return RecordVerification(
            ok=False, stage="prereg", problems=[f"{RECORD_PATH}: {e}"]
        )

    try:
        metrics_data = load_metrics_data(str(root))
    except ValueError:
        metrics_data = {}

    reported_run_ids = runs_with_reports(root, record)
    stage: Literal["prereg", "results"] = (
        "results" if metrics_data or reported_run_ids else "prereg"
    )

    problems = await asyncio.to_thread(verify_record_offline, root, record)
    # Every committed version is held to the declaration checks too: a
    # declaration may only name passages already in the record when it lands.
    problems += await asyncio.to_thread(
        verify_record_history, root, record, require_history, verify_record_declarations
    )

    provenance: _ProvenanceCheckResult | None = None
    problems += await asyncio.to_thread(
        verify_run_results, root, record, metrics_data, reported_run_ids, stage
    )
    if stage == "results":
        if check_provenance and (
            scope := provenance_scope(record, metrics_data, reported_run_ids)
        ):
            provenance = await verify_results_against_store(
                str(root), scope, store_factory
            )
        if reported_run_ids:
            # Turning the check off is a decision not to require it.
            problems += provenance_problems(
                provenance, require_provenance and check_provenance
            )
    return RecordVerification(
        ok=not problems,
        stage=stage,
        problems=problems,
        provenance=provenance.model_dump() if provenance else None,
    )
