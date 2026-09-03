from __future__ import annotations

from pathlib import Path
from typing import Literal

from pydantic import ValidationError

from airas.core.research_paths import RECORD_PATH
from airas.core.types.paper_values import ClaimRunCheck, ClaimStatus
from airas.core.types.research_record import ResearchRecord
from airas.core.types.run_provenance import RunProvenanceManifest
from airas.infra.local_git import (
    commit_is_ancestor,
    commits_touching,
    file_bytes_at_commit,
    is_shallow,
)
from airas.usecases.publication.paper_values.compute import COMPARISON_KEY
from airas.usecases.publication.paper_values.record import (
    active,
    record_append_violations,
    ref_run_id,
    run_index,
    selected_execution,
)

APPEND_ONLY_STATUS = Literal["ok", "violated", "unavailable"]


def _record_at_commit(
    repo_root: Path, commit_hash: str, cache: dict[str, ResearchRecord | None]
) -> ResearchRecord | None:
    if commit_hash not in cache:
        raw = file_bytes_at_commit(repo_root, commit_hash, RECORD_PATH)
        try:
            cache[commit_hash] = (
                None if raw is None else ResearchRecord.model_validate_json(raw)
            )
        except ValidationError:
            cache[commit_hash] = None
    return cache[commit_hash]


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
    repo_root: Path,
    record: ResearchRecord,
    manifest: RunProvenanceManifest | None,
    present_dirs: set[str],
    claim_values: dict[str, tuple[float, str, dict[str, str]]] | None = None,
) -> list[ClaimStatus]:
    """Recompute each claim's status from git, provenance and the results.

    `verified` and `criterion_met` answer different questions and are kept
    apart on purpose: a claim can be properly preregistered, executed and
    checked — verified — and still have missed its criterion. That is a
    negative result, not a failure of the record, and reading five
    `verified: true` flags as "the hypothesis held" is exactly the misreading
    the second field exists to prevent.
    """
    runs_by_id = run_index(record)
    record_cache: dict[str, ResearchRecord | None] = {}
    statuses: list[ClaimStatus] = []

    for claim in active(record.hypothesis.claims, "id"):
        checks: list[ClaimRunCheck] = []
        for run_id in sorted({ref_run_id(r) for r in claim.target.refs}):
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
                (c for c in past.hypothesis.claims if c.id == claim.id), None
            )
            past_run = (
                next(
                    (r for r in run_index(past).values() if r.run_id == run_id),
                    None,
                )
                if past
                else None
            )
            current_run = runs_by_id.get(run_id)
            # Only the declaration is compared: executions are appended after
            # the run, so requiring the whole run entry to match would make
            # every claim unverifiable the moment its results arrived.
            claim_predates_run = bool(
                past_claim
                and past_claim.model_dump(exclude={"evaluations"})
                == claim.model_dump(exclude={"evaluations"})
            )
            if run_id == COMPARISON_KEY:
                # The comparison directory is derived from the other runs by
                # the aggregation step, so no run declares it and there is no
                # run entry to match. Requiring one would leave every claim
                # that cites an aggregate permanently unverified. The part
                # that carries the guarantee — the claim already existed at
                # the commit the run executed — is still checked.
                check.declared_at_run_commit = claim_predates_run
            else:
                check.declared_at_run_commit = bool(
                    claim_predates_run
                    and past_run
                    and current_run
                    and past_run.model_dump(exclude={"executions"})
                    == current_run.model_dump(exclude={"executions"})
                )
            if not check.declared_at_run_commit:
                check.detail = (
                    "record.json is unreadable at the run commit"
                    if past is None
                    else "the identical claim and run declarations did not "
                    "exist at the run commit"
                )

        measured = (claim_values or {}).get(claim.id)
        value = measured[0] if measured else None
        statuses.append(
            ClaimStatus(
                id=claim.id,
                verified=bool(checks) and all(c.declared_at_run_commit for c in checks),
                criterion_met=(
                    claim.criterion.contains(value) if value is not None else None
                ),
                value=value,
                display=measured[1] if measured else None,
                used_executions=measured[2] if measured else {},
                checks=checks,
            )
        )
    return statuses


def design_rollup(record: ResearchRecord) -> dict[str, dict[str, int]]:
    """Per-design completeness, derived rather than stored.

    Answers "was the experiment for this design actually carried out" without
    keeping a flag that could drift from the runs it summarises.
    """
    rollup: dict[str, dict[str, int]] = {}
    for design in active(record.hypothesis.designs, "id"):
        runs = active(design.runs, "run_id")
        rollup[design.id] = {
            "runs": len(runs),
            "executed": sum(1 for r in runs if selected_execution(r) is not None),
        }
    return rollup
