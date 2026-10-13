"""The record gate: is record.json what was declared, whole, and backed by
the run outputs? Composes the checks in the `_verify_*` modules."""

from __future__ import annotations

import asyncio
from pathlib import Path
from typing import Literal

from pydantic import ValidationError

from airas.core.research_paths import RECORD_PATH, RESULTS_DIR, repo_root
from airas.core.types.record_verification import RecordVerification
from airas.core.types.research_record import ResearchRecord
from airas.infra.litellm_client import LiteLLMClient
from airas.infra.local_git import commit_paths
from airas.infra.run_output_store import default_store
from airas.research_record.llm_as_a_judge.judge_implementation_against_design import (
    judge_implementation_against_design,
)
from airas.research_record.read.declaration_paths import declaration_paths
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
    verification = RecordVerification()
    verify_record_in_itself(record, verification)
    verify_quoted_passages(root, record, verification)
    return verification.problems


def _append_provenance_statuses(
    record: ResearchRecord,
    scope: set[str],
    provenance: _ProvenanceCheckResult,
    verification: RecordVerification,
) -> None:
    result_paths = {
        run.run_id: f"hypotheses[{h.id}]/claims[{c.id}]/designs[{d.id}]"
        f"/runs[{run.run_id}]/results[{run.results[-1].id}]"
        for h, c, d, run in record.latest_runs()
        if run.results
    }
    if provenance.status == "unavailable":
        for dir_name in sorted(scope):
            verification.append_declaration_status(
                result_paths.get(dir_name, f"{RESULTS_DIR}/{dir_name}"),
                f"{provenance.source} stored outputs unavailable: {provenance.detail}",
                "skipped",
            )
        return
    for check in provenance.checks:
        siblings = (
            f"; other completed runs of the same commit: {', '.join(check.sibling_run_ids)}"
            if check.sibling_run_ids
            else ""
        )
        verification.append_declaration_status(
            result_paths.get(check.dir, f"{RESULTS_DIR}/{check.dir}"),
            f"{provenance.source} stored outputs of run {check.run_id}: {check.detail}{siblings}"
            if check.matched
            else f"{provenance.source}: {RESULTS_DIR}/{check.dir} is not backed by stored "
            f"run outputs — {check.detail}",
            "ok" if check.matched else "mismatch",
        )


def _append_unchecked_declarations(
    record: ResearchRecord, verification: RecordVerification
) -> None:
    noted = {s.path for s in verification.declaration_statuses}
    compared = [
        s.path for s in verification.declaration_statuses if s.status != "skipped"
    ]
    for path in declaration_paths(record):
        if path in noted or any(path.startswith(c + "/") for c in compared):
            continue
        verification.append_declaration_status(path, "no check", "skipped")


async def verify_record(
    local_path: str,
    *,
    check_provenance: bool = True,
    require_provenance: bool = True,
    require_history: bool = True,
    store_factory: StoreFactory = default_store,
    implementation_verifier_model: str | None = None,
    litellm_client: LiteLLMClient | None = None,
) -> RecordVerification:
    root = repo_root(local_path)
    verification = RecordVerification()

    try:
        record = load_record(str(root))
    except (ValidationError, ValueError) as e:
        verification.append_declaration_status(
            RECORD_PATH, f"{RECORD_PATH}: {e}", "mismatch"
        )
        return verification

    try:
        metrics_data = load_metrics_data(str(root))
    except ValueError:
        metrics_data = {}

    reported_run_ids = run_ids_with_verifier_report(root, record)

    stage: Literal["prereg", "results"] = (
        "results" if metrics_data or reported_run_ids else "prereg"
    )
    verification.stage = stage

    verify_record_in_itself(record, verification)
    await asyncio.to_thread(verify_quoted_passages, root, record, verification)

    # Every committed version is held to the declaration checks too: a
    # declaration may only name passages already in the record when it lands.
    await asyncio.to_thread(
        verify_record_git_history,
        root,
        record,
        require_history,
        verify_record_in_itself,
        verification,
    )

    await asyncio.to_thread(
        verify_run_results,
        root,
        record,
        metrics_data,
        reported_run_ids,
        stage,
        verification,
    )

    if stage == "results":
        await asyncio.to_thread(verify_run_observations, root, record, verification)
        reviewed = await judge_implementation_against_design(
            root,
            record,
            verification,
            model=implementation_verifier_model,
            litellm_client=litellm_client,
        )
        if reviewed:
            record.save(str(root))
            commit_paths(root, [RECORD_PATH], "record: review implementation")

        provenance: _ProvenanceCheckResult | None = None
        if check_provenance and (
            scope := provenance_scope(record, metrics_data, reported_run_ids)
        ):
            provenance = await verify_results_against_store(
                str(root), scope, store_factory
            )
            _append_provenance_statuses(record, scope, provenance, verification)

        # Turning the check off is a decision not to require it.
        if reported_run_ids and require_provenance and check_provenance:
            if provenance is None:
                verification.append_declaration_status(
                    RECORD_PATH,
                    "the provenance cross-check did not run (record.json references "
                    "no results directories, or the check was disabled)",
                    "mismatch",
                )
            elif provenance.status == "unavailable":
                verification.append_declaration_status(
                    RECORD_PATH,
                    f"provenance unavailable: {provenance.detail}",
                    "mismatch",
                )

    _append_unchecked_declarations(record, verification)
    return verification
