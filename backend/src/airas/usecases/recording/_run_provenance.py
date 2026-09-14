from __future__ import annotations

import hashlib
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
    ResultsDirProvenance,
)
from airas.infra.local_git import commit_is_ancestor, remote_origin_url
from airas.infra.run_output_store import (
    COMPLETED_STATUS,
    RunExpired,
    RunOutputStore,
    StoredRun,
    default_store,
)
from airas.usecases.recording.update_or_load_record import load_provenance_manifest

StoreFactory = Callable[[str, str], RunOutputStore]


class _ProvenanceDirCheck(BaseModel):
    dir: str = Field(description="Directory name under .research/results/")
    backend: str | None = None
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
            "its dispatch parameters match the manifest where the backend "
            "reported them (see parameters_match), and its commit is an "
            "ancestor of HEAD"
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
            "The manifest's cached overrides/parameters equal what the backend "
            "recorded for the dispatch; None when it reported none"
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
    source: str = Field(description="The backends consulted, e.g. 'seyval'")
    status: Literal["verified", "mismatch", "unavailable"] = Field(
        description=(
            "verified: every referenced directory is backed by a completed "
            "run's stored bytes; mismatch: at least one is not (tampering "
            "or unknown provenance); unavailable: the backend could not "
            "be consulted (no credentials, no registered repository, "
            "network)"
        )
    )
    checks: list[_ProvenanceDirCheck] = Field(default_factory=list)
    detail: str = ""


async def verify_run_provenance(
    local_repo_path: str,
    used_dirs: set[str],
    store_factory: StoreFactory = default_store,
) -> _ProvenanceCheckResult:
    """Cross-check local results directories against the backends' stored run outputs."""
    try:
        return await _cross_check(store_factory, local_repo_path, used_dirs)
    except Exception as e:
        return _unavailable(f"provenance verifier unavailable: {e}")


async def _cross_check(
    store_factory: StoreFactory, local_repo_path: str, used_dirs: set[str]
) -> _ProvenanceCheckResult:
    root = Path(local_repo_path).expanduser().resolve()

    manifest = load_provenance_manifest(root)
    if manifest is None:
        return _ProvenanceCheckResult(
            source="none",
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
        return _unavailable("local clone has no 'origin' remote to match against")

    backends = sorted(
        {manifest.dirs[d].backend for d in used_dirs if d in manifest.dirs}
    )
    stores: dict[str, tuple[RunOutputStore, list[StoredRun]]] = {}
    for backend in backends:
        try:
            store = store_factory(backend, remote_url)
            stores[backend] = (store, await store.alist_runs())
        except Exception as e:
            return _unavailable(f"could not list {backend} runs: {e}")

    checks = []
    for dir_name in sorted(used_dirs):
        declared = manifest.dirs.get(dir_name)
        if declared is None:
            checks.append(
                _ProvenanceDirCheck(
                    dir=dir_name,
                    matched=False,
                    detail=f"{PROVENANCE_MANIFEST_PATH} declares no run for this directory",
                )
            )
            continue
        store, listed_runs = stores[declared.backend]
        checks.append(await _check_dir(store, root, dir_name, declared, listed_runs))

    all_matched = all(c.matched for c in checks)
    failed = [c.dir for c in checks if not c.matched]
    return _ProvenanceCheckResult(
        source=",".join(backends) or "none",
        status="verified" if all_matched else "mismatch",
        checks=checks,
        detail=("" if all_matched else f"unbacked directories: {', '.join(failed)}"),
    )


async def _check_dir(
    store: RunOutputStore,
    root: Path,
    dir_name: str,
    declared: ResultsDirProvenance,
    listed_runs: list[StoredRun],
) -> _ProvenanceDirCheck:
    execution_id = declared.execution_id
    backend = store.backend

    def fail(detail: str, **fields: Any) -> _ProvenanceDirCheck:
        return _ProvenanceDirCheck(
            dir=dir_name, matched=False, detail=detail, **{"backend": backend, **fields}
        )

    repo_path = _metrics_repo_path(dir_name)
    if not (root / repo_path).is_file():
        return fail(f"local file missing: {repo_path}", run_id=execution_id)

    run = next((r for r in listed_runs if r.execution_id == execution_id), None)
    if run is None:
        return fail(
            f"declared run {execution_id} is not among this repository's "
            f"{backend} runs (a very old run may have aged out of the listing)",
            run_id=execution_id,
        )
    if run.status != COMPLETED_STATUS:
        return fail(
            f"declared run {execution_id} is not completed (status: {run.status})",
            run_id=execution_id,
        )
    # The claim-order check derives from the manifest's commit_hash, so a
    # manifest pointing at a later commit must not survive this cross-check.
    commit_hash = run.commit_hash or ""
    if declared.commit_hash and commit_hash and declared.commit_hash != commit_hash:
        return fail(
            f"{PROVENANCE_MANIFEST_PATH} declares commit "
            f"{declared.commit_hash[:12]} for run {execution_id}, but "
            f"{backend} recorded {commit_hash[:12]}",
            run_id=execution_id,
            commit_hash=commit_hash,
        )

    parameters_match: bool | None = None
    if run.overrides is not None or run.parameters is not None:
        parameters_match = (
            run.overrides is None or dict(declared.overrides) == run.overrides
        ) and (run.parameters is None or dict(declared.parameters) == run.parameters)
        if not parameters_match:
            return fail(
                f"{PROVENANCE_MANIFEST_PATH} caches dispatch parameters for "
                f"run {execution_id} that differ from what {backend} recorded",
                run_id=execution_id,
                commit_hash=commit_hash or None,
                parameters_match=False,
            )

    sibling_run_ids = [
        r.execution_id
        for r in listed_runs
        if r.status == COMPLETED_STATUS
        and r.execution_id != execution_id
        and commit_hash
        and r.commit_hash == commit_hash
    ]
    common: dict[str, Any] = {
        "backend": backend,
        "run_id": execution_id,
        "commit_hash": commit_hash or None,
        "sibling_run_ids": sibling_run_ids,
        "parameters_match": parameters_match,
    }

    try:
        stored = await store.alist_outputs(execution_id)
    except RunExpired as e:
        return _check_expired(root, dir_name, declared, str(e), common)
    except Exception as e:
        return fail(f"could not list run outputs: {e}", run_id=execution_id)
    if repo_path not in stored:
        return fail(
            f"declared run {execution_id} did not produce {repo_path}",
            run_id=execution_id,
        )

    local_paths = _local_paths(root, dir_name)
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
            **common,
        )
    files_checked: list[str] = []
    for local_repo_path in local_paths:
        if local_repo_path not in stored:
            return fail(
                f"local {local_repo_path} exists but the declared run "
                f"{execution_id} produced no such file",
                files_checked=files_checked,
                **common,
            )
        try:
            remote_bytes = await store.adownload(execution_id, local_repo_path)
        except Exception as e:
            return fail(
                f"could not download stored output {local_repo_path}: {e}",
                files_checked=files_checked,
                **common,
            )
        if remote_bytes != (root / local_repo_path).read_bytes():
            return fail(
                f"local {local_repo_path} differs from the bytes the "
                f"declared run {execution_id} actually produced",
                files_checked=files_checked,
                **common,
            )
        files_checked.append(local_repo_path)

    return _anchored(
        root,
        dir_name,
        files_checked,
        f"{len(files_checked)} file(s) byte-identical to the declared run's stored outputs",
        common,
    )


def _check_expired(
    root: Path,
    dir_name: str,
    declared: ResultsDirProvenance,
    reason: str,
    common: dict[str, Any],
) -> _ProvenanceDirCheck:
    def fail(detail: str) -> _ProvenanceDirCheck:
        return _ProvenanceDirCheck(dir=dir_name, matched=False, detail=detail, **common)

    if not declared.files:
        return fail(
            f"{reason}, and {PROVENANCE_MANIFEST_PATH} carries no import-time "
            "hashes for this directory — re-import while the backend holds the run"
        )
    prefix = f"{RESULTS_DIR}/{dir_name}/"
    expected = {p: h for p, h in declared.files.items() if p.startswith(prefix)}
    local_paths = _local_paths(root, dir_name)
    if set(local_paths) != set(expected):
        return fail(
            f"{reason}; the local directory does not hold exactly the files "
            "the import declared"
        )
    for path in local_paths:
        if hashlib.sha256((root / path).read_bytes()).hexdigest() != expected[path]:
            return fail(f"{reason}; local {path} differs from the import-time hash")
    return _anchored(
        root,
        dir_name,
        local_paths,
        f"{reason}; {len(local_paths)} file(s) match the import-time hashes",
        common,
    )


def _anchored(
    root: Path,
    dir_name: str,
    files_checked: list[str],
    detail: str,
    common: dict[str, Any],
) -> _ProvenanceDirCheck:
    commit_hash = common.get("commit_hash") or ""
    commit_ok = bool(commit_hash) and commit_is_ancestor(root, commit_hash)
    return _ProvenanceDirCheck(
        dir=dir_name,
        commit_in_history=commit_ok,
        matched=commit_ok,
        files_checked=files_checked,
        detail=(
            detail
            if commit_ok
            else (
                f"{detail}, but its commit {commit_hash[:12] or '<missing>'} is "
                "not an ancestor of the local HEAD"
            )
        ),
        **common,
    )


def _local_paths(root: Path, dir_name: str) -> list[str]:
    # Every file, not only metrics.json: the inputs the metrics derive from
    # and the evaluator's report are anchored too. POSIX form, as the backends
    # report it.
    dir_root = root / RESULTS_DIR / dir_name
    return sorted(
        path.relative_to(root).as_posix()
        for path in dir_root.rglob("*")
        if path.is_file()
    )


def _unavailable(detail: str) -> _ProvenanceCheckResult:
    return _ProvenanceCheckResult(source="none", status="unavailable", detail=detail)


def _metrics_repo_path(dir_name: str) -> str:
    filename = (
        COMPARISON_METRICS_FILENAME if dir_name == COMPARISON_KEY else METRICS_FILENAME
    )
    return f"{RESULTS_DIR}/{dir_name}/{filename}"
