from __future__ import annotations

from pathlib import Path
from typing import Any, Callable, Literal

from pydantic import BaseModel, Field

from airas.core.research_paths import (
    COMPARISON_KEY,
    COMPARISON_METRICS_FILENAME,
    METRICS_FILENAME,
    RESULTS_DIR,
)
from airas.core.types.run_provenance import (
    PROVENANCE_MANIFEST_PATH,
    RunProvenanceManifest,
)
from airas.infra.local_git import (
    commit_is_ancestor,
    normalize_git_url,
    remote_origin_url,
)
from airas.infra.seyval_client import (
    SeyvalClient,
    default_seyval_client,
    parse_overrides,
    parse_parameters,
)
from airas.usecases.recording.update_or_load_record import load_provenance_manifest

SOURCE = "seyval"

COMPLETED_STATUS = "completed"


class _ProvenanceDirCheck(BaseModel):
    dir: str = Field(description="Directory name under .research/results/")
    run_id: str | None = Field(
        default=None,
        description=(
            "Platform run the provenance manifest declares for this directory"
        ),
    )
    commit_hash: str | None = Field(
        default=None, description="Commit that run executed"
    )
    commit_in_history: bool | None = Field(
        default=None,
        description=("Whether that commit is an ancestor of the local clone's HEAD"),
    )
    matched: bool = Field(
        description=(
            "The declared, completed run holds byte-identical copies of every "
            "file in this directory and produced no file the directory lacks, "
            "its dispatch parameters match the manifest where Seyval reported "
            "them (see parameters_match), and its commit is an ancestor of HEAD"
        )
    )
    files_checked: list[str] = Field(
        default_factory=list,
        description=(
            "Repository-relative paths byte-compared against the run's stored "
            "outputs — every file under the directory, not only metrics.json, "
            "so the inputs the metrics derive from are anchored too"
        ),
    )
    parameters_match: bool | None = Field(
        default=None,
        description=(
            "The manifest's cached overrides/parameters equal what Seyval "
            "recorded for the dispatch; None when Seyval reported none"
        ),
    )
    sibling_run_ids: list[str] = Field(
        default_factory=list,
        description=(
            "Other completed runs of the same commit — the same code was "
            "executed more than once, so which run backs the paper was a "
            "choice; listed to make that choice reviewable"
        ),
    )
    detail: str = ""


class _ProvenanceCheckResult(BaseModel):
    source: str = Field(description="The platform consulted, e.g. 'seyval'")
    status: Literal["verified", "mismatch", "unavailable"] = Field(
        description=(
            "verified: every referenced directory is backed by a completed "
            "run's stored bytes; mismatch: at least one is not (tampering "
            "or unknown provenance); unavailable: the platform could not "
            "be consulted (no credentials, no registered repository, "
            "network)"
        )
    )
    checks: list[_ProvenanceDirCheck] = Field(default_factory=list)
    detail: str = ""


async def verify_seyval_provenance(
    local_repo_path: str,
    used_dirs: set[str],
    seyval_client_factory: Callable[[], SeyvalClient] = default_seyval_client,
) -> _ProvenanceCheckResult:
    """Cross-check local results directories against Seyval's stored run outputs."""
    try:
        return await _cross_check(seyval_client_factory(), local_repo_path, used_dirs)
    except Exception as e:
        return _unavailable(f"provenance verifier unavailable: {e}")


async def _cross_check(
    client: SeyvalClient, local_repo_path: str, used_dirs: set[str]
) -> _ProvenanceCheckResult:
    root = Path(local_repo_path).expanduser().resolve()

    manifest = load_provenance_manifest(root)
    if manifest is None:
        # Without a declaration there is nothing to pin the data to —
        # however the files got here, their provenance is unknown.
        return _ProvenanceCheckResult(
            source=SOURCE,
            status="mismatch",
            checks=[
                _ProvenanceDirCheck(
                    dir=dir_name,
                    matched=False,
                    detail=(
                        f"no readable {PROVENANCE_MANIFEST_PATH} declares "
                        "which run produced this directory (import the "
                        "results with import_run_outputs)"
                    ),
                )
                for dir_name in sorted(used_dirs)
            ],
            detail=f"missing or unreadable {PROVENANCE_MANIFEST_PATH}",
        )

    remote_url = remote_origin_url(root)
    if not remote_url:
        return _unavailable(
            "local clone has no 'origin' remote to match against Seyval"
        )
    normalized = normalize_git_url(remote_url)

    try:
        repositories = await client.alist_repositories()
    except Exception as e:  # network / auth — degrade explicitly
        return _unavailable(f"could not list Seyval repositories: {e}")

    repo_ids = [
        r["id"]
        for r in repositories
        if normalize_git_url(str(r.get("git_url", ""))) == normalized
    ]
    if not repo_ids:
        return _unavailable(f"no Seyval repository registered for {normalized}")

    # The repository's own run listing is the only source consulted, so
    # a declared run is accepted only if this repository actually ran it.
    listed_runs: list[dict[str, Any]] = []
    try:
        for repo_id in repo_ids:
            listed_runs.extend(await client.alist_runs(repo_id))
    except Exception as e:
        return _unavailable(f"could not list Seyval runs: {e}")

    # Several directories usually declare the same run (each run dir
    # plus comparison/), so its outputs listing is fetched once. The
    # dirs are checked sequentially: their count is small, and the
    # bulk of the wall clock is the per-run download, deduplicated by
    # this cache rather than by concurrency.
    outputs_cache: dict[str, dict[str, Any]] = {}
    checks = [
        await _check_dir(client, root, dir_name, manifest, listed_runs, outputs_cache)
        for dir_name in sorted(used_dirs)
    ]

    all_matched = all(c.matched for c in checks)
    failed = [c.dir for c in checks if not c.matched]
    return _ProvenanceCheckResult(
        source=SOURCE,
        status="verified" if all_matched else "mismatch",
        checks=checks,
        detail=("" if all_matched else f"unbacked directories: {', '.join(failed)}"),
    )


async def _check_dir(
    client: SeyvalClient,
    root: Path,
    dir_name: str,
    manifest: RunProvenanceManifest,
    listed_runs: list[dict[str, Any]],
    outputs_cache: dict[str, dict[str, Any]],
) -> _ProvenanceDirCheck:
    def fail(detail: str, **fields: Any) -> _ProvenanceDirCheck:
        return _ProvenanceDirCheck(dir=dir_name, matched=False, detail=detail, **fields)

    declared = manifest.dirs.get(dir_name)
    if declared is None:
        return fail(f"{PROVENANCE_MANIFEST_PATH} declares no run for this directory")
    execution_id = declared.execution_id

    repo_path = _metrics_repo_path(dir_name)
    local_file = root / repo_path
    if not local_file.is_file():
        return fail(f"local file missing: {repo_path}", run_id=execution_id)

    run = next(
        (r for r in listed_runs if str(r.get("run_id", "")) == execution_id),
        None,
    )
    if run is None:
        return fail(
            f"declared run {execution_id} is not among this repository's "
            "Seyval runs (a very old run may have aged out of the listing)",
            run_id=execution_id,
        )
    if run.get("status") != COMPLETED_STATUS:
        return fail(
            f"declared run {execution_id} is not completed "
            f"(status: {run.get('status')})",
            run_id=execution_id,
        )
    # The claim-order check derives from the manifest's commit_hash, so a
    # manifest pointing at a later commit (one that already contains a
    # post-hoc claim) must not survive this cross-check.
    seyval_commit = str(run.get("commit_hash") or "")
    if declared.commit_hash and seyval_commit and declared.commit_hash != seyval_commit:
        return fail(
            f"{PROVENANCE_MANIFEST_PATH} declares commit "
            f"{declared.commit_hash[:12]} for run {execution_id}, but "
            f"Seyval recorded {seyval_commit[:12]}",
            run_id=execution_id,
            commit_hash=seyval_commit,
        )

    # The manifest caches what the dispatch was given so the record can
    # be realized offline; the cache must equal the platform's record,
    # or a declared `mode=full` could be "confirmed" by a cache that says
    # so while Seyval says `pilot`.
    # "Reported" is decided by the field being present, not by the parsed
    # result being non-empty: a dispatch with no overrides is a report
    # of "none", and a cache that claims some must then be wrong.
    # Absent fields mean the platform did not say, and are not compared.
    reports_overrides = run.get("command_args") is not None
    reports_parameters = (
        run.get("resolved_parameters") is not None or run.get("parameters") is not None
    )
    parameters_match: bool | None = None
    if reports_overrides or reports_parameters:
        parameters_match = (
            not reports_overrides
            or dict(declared.overrides) == parse_overrides(run.get("command_args"))
        ) and (
            not reports_parameters or dict(declared.parameters) == parse_parameters(run)
        )
        if not parameters_match:
            return fail(
                f"{PROVENANCE_MANIFEST_PATH} caches dispatch parameters for "
                f"run {execution_id} that differ from what Seyval recorded",
                run_id=execution_id,
                commit_hash=seyval_commit or None,
                parameters_match=False,
            )

    listing = outputs_cache.get(execution_id)
    if listing is None:
        try:
            listing = await client.aget_run_outputs(execution_id)
        except Exception as e:
            return fail(f"could not list run outputs: {e}", run_id=execution_id)
        outputs_cache[execution_id] = listing
    stored = {
        str(item.get("path")): item
        for item in listing.get("outputs") or []
        if item.get("path")
    }
    if repo_path not in stored:
        return fail(
            f"declared run {execution_id} did not produce {repo_path}",
            run_id=execution_id,
        )

    commit_hash = seyval_commit
    sibling_run_ids = [
        str(r.get("run_id", ""))
        for r in listed_runs
        if r.get("status") == COMPLETED_STATUS
        and str(r.get("run_id", "")) != execution_id
        and commit_hash
        and str(r.get("commit_hash") or "") == commit_hash
    ]

    # Every file under the directory, not only the metrics: the inputs
    # the metrics were derived from and the evaluator's report are what
    # make the metrics re-derivable, so an unanchored copy of either
    # would leave the record's inputs hash pointing at a file anyone
    # could have written.
    dir_root = root / RESULTS_DIR / dir_name
    # Seyval reports POSIX paths; compare on the same form regardless of
    # the host's separator.
    local_paths = sorted(
        path.relative_to(root).as_posix()
        for path in dir_root.rglob("*")
        if path.is_file()
    )
    # Both directions. A file the run produced that is missing locally is
    # as much a divergence as one the run never produced: deleting the
    # evaluator's report, say, would erase its `skipped` verdicts and
    # leave the record's evaluation field an honest-looking None.
    prefix = f"{RESULTS_DIR}/{dir_name}/"
    missing_locally = sorted(
        path
        for path in stored
        if path.startswith(prefix) and not (root / path).is_file()
    )
    if missing_locally:
        return fail(
            f"the declared run {execution_id} produced "
            f"{', '.join(missing_locally)} but the local directory does "
            "not hold it (deleted after import?)",
            run_id=execution_id,
            commit_hash=commit_hash or None,
            parameters_match=parameters_match,
        )
    files_checked: list[str] = []
    for local_repo_path in local_paths:
        entry = stored.get(local_repo_path)
        if entry is None:
            return fail(
                f"local {local_repo_path} exists but the declared run "
                f"{execution_id} produced no such file",
                run_id=execution_id,
                commit_hash=commit_hash or None,
                files_checked=files_checked,
                parameters_match=parameters_match,
            )
        try:
            remote_bytes = await client.adownload(entry["download_url"])
        except Exception as e:
            return fail(
                f"could not download stored output {local_repo_path}: {e}",
                run_id=execution_id,
                files_checked=files_checked,
                parameters_match=parameters_match,
            )
        if remote_bytes != (root / local_repo_path).read_bytes():
            return fail(
                f"local {local_repo_path} differs from the bytes the "
                f"declared run {execution_id} actually produced",
                run_id=execution_id,
                commit_hash=commit_hash or None,
                sibling_run_ids=sibling_run_ids,
                files_checked=files_checked,
                parameters_match=parameters_match,
            )
        files_checked.append(local_repo_path)

    commit_ok = bool(commit_hash) and commit_is_ancestor(root, commit_hash)
    return _ProvenanceDirCheck(
        dir=dir_name,
        run_id=execution_id,
        commit_hash=commit_hash or None,
        commit_in_history=commit_ok,
        matched=commit_ok,
        sibling_run_ids=sibling_run_ids,
        files_checked=files_checked,
        parameters_match=parameters_match,
        detail=(
            f"{len(files_checked)} file(s) byte-identical to the declared "
            "run's stored outputs"
            if commit_ok
            else (
                f"bytes match run {execution_id}, but its commit "
                f"{commit_hash[:12] or '<missing>'} is not an ancestor of "
                "the local HEAD"
            )
        ),
    )


def _unavailable(detail: str) -> _ProvenanceCheckResult:
    return _ProvenanceCheckResult(source=SOURCE, status="unavailable", detail=detail)


def _metrics_repo_path(dir_name: str) -> str:
    filename = (
        COMPARISON_METRICS_FILENAME if dir_name == COMPARISON_KEY else METRICS_FILENAME
    )
    return f"{RESULTS_DIR}/{dir_name}/{filename}"
