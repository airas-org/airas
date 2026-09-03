from __future__ import annotations

from pathlib import Path
from typing import Literal

from pydantic import ValidationError

from airas.core.research_paths import RECORD_PATH
from airas.core.types.paper_values import ClaimRunCheck, ClaimStatus
from airas.core.types.research_record import ResearchRecord
from airas.infra.local_git import (
    commits_touching,
    file_bytes_at_commit,
    is_shallow,
)
from airas.usecases.publication.paper_values.record import (
    all_claims,
    claim_runs,
    record_append_violations,
)

APPEND_ONLY_STATUS = Literal["ok", "violated", "unavailable"]


def record_append_only_status(
    repo_root: Path, current: ResearchRecord
) -> tuple[APPEND_ONLY_STATUS, list[str], list[str]]:
    # Returns (status, problems, record commits oldest-first — first = freeze).
    if is_shallow(repo_root):
        return "unavailable", ["shallow clone: record.json history is truncated"], []
    commit_hashes = commits_touching(repo_root, RECORD_PATH)
    if commit_hashes is None:
        return "unavailable", ["git history could not be read"], []
    oldest_first = list(reversed(commit_hashes))

    versions: list[tuple[str, ResearchRecord]] = []
    for commit_hash in oldest_first:
        raw = file_bytes_at_commit(repo_root, commit_hash, RECORD_PATH)
        if raw is None:
            continue  # the commit deleted the file
        try:
            versions.append((commit_hash, ResearchRecord.model_validate_json(raw)))
        except ValidationError:
            return (
                "violated",
                [f"record.json at {commit_hash[:12]} is not a valid record"],
                oldest_first,
            )
    versions.append(("worktree", current))

    problems = [
        f"{older_hash[:12]} -> {newer_hash[:12]}: {problem}"
        for (older_hash, older), (newer_hash, newer) in zip(
            versions, versions[1:], strict=False
        )
        for problem in record_append_violations(older, newer)
    ]
    return ("violated" if problems else "ok"), problems, oldest_first


def compute_claim_status(
    record: ResearchRecord, present_dirs: set[str]
) -> list[ClaimStatus]:
    """Is every run under each claim executed?

    `verified` means the claim's experiments are all done: every run under
    its designs has a results directory with metrics. That is the whole
    condition for now. Whether the claim was declared before those runs
    executed (the order proof) and whether its condition was met are not
    modelled yet — TODO — so the flag says "the data this claim rests on
    is in", not "the claim held" and not yet "the claim was preregistered".
    What already guards the rest: containment forbids changing a declaration
    once committed, and the provenance check requires each run's commit to
    be an ancestor of HEAD.
    """
    statuses: list[ClaimStatus] = []
    for _, claim in all_claims(record):
        checks = [
            ClaimRunCheck(
                run_id=run.run_id,
                results_present=run.run_id in present_dirs,
                detail=(
                    ""
                    if run.run_id in present_dirs
                    else "no results directory with metrics for this run"
                ),
            )
            for _, run in claim_runs(claim)
        ]
        statuses.append(
            ClaimStatus(
                id=claim.id,
                verified=bool(checks) and all(c.results_present for c in checks),
                checks=checks,
            )
        )
    return statuses
