from __future__ import annotations

from pathlib import Path
from typing import Literal

from pydantic import ValidationError

from airas.core.research_paths import RECORD_PATH
from airas.core.types.paper_record import PaperRecord
from airas.core.types.paper_values import ClaimRunCheck, ClaimStatus
from airas.core.types.run_provenance import RunProvenanceManifest
from airas.infra.local_git import (
    commit_is_ancestor,
    commits_touching,
    file_bytes_at_commit,
    is_shallow,
)
from airas.usecases.publication.paper_values.record import (
    active,
    prereg_append_violations,
)

APPEND_ONLY_STATUS = Literal["ok", "violated", "unavailable"]


def _record_at_commit(
    repo_root: Path, commit_hash: str, cache: dict[str, PaperRecord | None]
) -> PaperRecord | None:
    if commit_hash not in cache:
        raw = file_bytes_at_commit(repo_root, commit_hash, RECORD_PATH)
        try:
            cache[commit_hash] = (
                None if raw is None else PaperRecord.model_validate_json(raw)
            )
        except ValidationError:
            cache[commit_hash] = None
    return cache[commit_hash]


def record_append_only_status(
    repo_root: Path, current: PaperRecord
) -> tuple[APPEND_ONLY_STATUS, list[str], list[str]]:
    # Returns (status, problems, record commits oldest-first — first = freeze).
    if is_shallow(repo_root):
        return "unavailable", ["shallow clone: record.json history is truncated"], []
    commit_hashes = commits_touching(repo_root, RECORD_PATH)
    if commit_hashes is None:
        return "unavailable", ["git history could not be read"], []
    oldest_first = list(reversed(commit_hashes))

    versions: list[tuple[str, PaperRecord]] = []
    for commit_hash in oldest_first:
        raw = file_bytes_at_commit(repo_root, commit_hash, RECORD_PATH)
        if raw is None:
            continue  # the commit deleted the file
        try:
            versions.append((commit_hash, PaperRecord.model_validate_json(raw)))
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
        for problem in prereg_append_violations(older.prereg, newer.prereg)
    ]
    return ("violated" if problems else "ok"), problems, oldest_first


def compute_claim_status(
    repo_root: Path,
    record: PaperRecord,
    manifest: RunProvenanceManifest | None,
    present_dirs: set[str],
) -> list[ClaimStatus]:
    runs_by_id = {r.run_id: r for r in record.prereg.runs}
    record_cache: dict[str, PaperRecord | None] = {}
    statuses: list[ClaimStatus] = []
    for claim in active(record.prereg.claims, "id"):
        checks: list[ClaimRunCheck] = []
        for run_id in claim.run_ids:
            check = ClaimRunCheck(run_id=run_id)
            checks.append(check)
            if run_id not in present_dirs:
                check.detail = "no results directory with metrics for this run"
                continue
            check.results_present = True
            declared = manifest.dirs.get(run_id) if manifest else None
            commit_hash = declared.commit_hash if declared else None
            if not commit_hash:
                check.detail = "no provenance commit declared for this run"
                continue
            check.run_commit = commit_hash
            check.commit_in_history = commit_is_ancestor(repo_root, commit_hash)
            if not check.commit_in_history:
                check.detail = "run commit is not an ancestor of HEAD"
                continue
            past = _record_at_commit(repo_root, commit_hash, record_cache)
            past_claim = past and next(
                (c for c in past.prereg.claims if c.id == claim.id), None
            )
            past_run = past and next(
                (r for r in past.prereg.runs if r.run_id == run_id), None
            )
            current_run = runs_by_id.get(run_id)
            check.declared_at_run_commit = bool(
                past_claim
                and past_claim.model_dump() == claim.model_dump()
                and past_run
                and current_run
                and past_run.model_dump() == current_run.model_dump()
            )
            if not check.declared_at_run_commit:
                check.detail = (
                    "record.json is unreadable at the run commit"
                    if past is None
                    else "the identical claim and run declarations did not "
                    "exist at the run commit"
                )
        statuses.append(
            ClaimStatus(
                id=claim.id,
                verified=all(c.declared_at_run_commit for c in checks),
                checks=checks,
            )
        )
    return statuses
