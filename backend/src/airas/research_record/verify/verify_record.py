"""The record gate: is record.json what was declared, whole, and backed by
the run outputs? Composes the checks in the `_verify_*` modules."""

from __future__ import annotations

import asyncio
from pathlib import Path
from typing import Literal

from pydantic import ValidationError

from airas.core.research_paths import RECORD_PATH, repo_root
from airas.core.types.record_verification import RecordVerification
from airas.core.types.research_record import ResearchRecord
from airas.infra.run_output_store import default_store
from airas.research_record.read.load_record import load_record
from airas.research_record.read.read_run_outputs import (
    load_metrics_data,
    run_ids_with_verifier_report,
)
from airas.research_record.verify._verify_quoted_passages import verify_quoted_passages
from airas.research_record.verify._verify_record_git_history import (
    verify_record_git_history,
)
from airas.research_record.verify._verify_record_in_itself import (
    verify_record_in_itself,
)
from airas.research_record.verify._verify_results_against_store import (
    StoreFactory,
    _ProvenanceCheckResult,
    provenance_problems,
    provenance_scope,
    verify_results_against_store,
)
from airas.research_record.verify._verify_run_observations import (
    verify_run_observations,
)
from airas.research_record.verify._verify_run_results import verify_run_results


# TODO: 循環依存が気になる
def verify_record_offline(root: Path, record: ResearchRecord) -> list[str]:
    """run の出力・git 履歴・実行基盤を使わず、作業ツリーだけで判定できる検査。書き込み側も保存前に呼ぶ。"""
    return verify_record_in_itself(record) + verify_quoted_passages(root, record)


async def verify_record(
    local_path: str,
    *,
    check_provenance: bool = True,
    require_provenance: bool = True,
    require_history: bool = True,
    store_factory: StoreFactory = default_store,
) -> RecordVerification:
    root = repo_root(local_path)
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

    reported_run_ids = run_ids_with_verifier_report(root, record)

    stage: Literal["prereg", "results"] = (
        "results" if metrics_data or reported_run_ids else "prereg"
    )

    problems = verify_record_in_itself(record)
    problems += await asyncio.to_thread(verify_quoted_passages, root, record)

    # Every committed version is held to the declaration checks too: a
    # declaration may only name passages already in the record when it lands.
    problems += await asyncio.to_thread(
        verify_record_git_history,
        root,
        record,
        require_history,
        verify_record_in_itself,
    )

    provenance: _ProvenanceCheckResult | None = None
    problems += await asyncio.to_thread(
        verify_run_results, root, record, metrics_data, reported_run_ids, stage
    )

    if stage == "results":
        problems += await asyncio.to_thread(verify_run_observations, root, record)
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
