from __future__ import annotations

import logging
import re
import subprocess
from pathlib import Path
from typing import Any

from pydantic import ValidationError

from airas.core.types.paper_values import ProvenanceCheckResult, ProvenanceDirCheck
from airas.core.types.run_provenance import (
    PROVENANCE_MANIFEST_PATH,
    RunProvenanceManifest,
)
from airas.infra.seyval_client import SeyvalClient
from airas.usecases.publication.paper_values.provenance import metrics_repo_path

logger = logging.getLogger(__name__)

SOURCE = "seyval"

COMPLETED_STATUS = "completed"


def _normalize_git_url(url: str) -> str:
    """Reduce the equivalent spellings of a repository URL to one form.

    An origin remote may be scp-like (git@host:org/repo.git) or a real
    ssh:// URL (ssh://git@host/org/repo.git); Seyval registers https.
    """
    url = url.strip().removesuffix(".git")
    match = re.match(r"git@([^:]+):(.+)$", url) or re.match(
        r"ssh://(?:[^@/]+@)?([^/:]+)(?::\d+)?/(.+)$", url
    )
    if match:
        url = f"https://{match.group(1)}/{match.group(2)}"
    return url.lower().rstrip("/")


def _local_remote_url(repo_root: Path) -> str | None:
    try:
        result = subprocess.run(
            ["git", "-C", str(repo_root), "remote", "get-url", "origin"],
            capture_output=True,
            text=True,
            timeout=30,
        )
    except (OSError, subprocess.TimeoutExpired):
        return None

    return result.stdout.strip() if result.returncode == 0 else None


def _commit_is_ancestor(repo_root: Path, commit_hash: str) -> bool:
    """Whether `commit_hash` is an ancestor of the local clone's HEAD.

    Ancestry, not mere existence: a commit on some unrelated local branch
    would "exist" in the clone, but only an ancestor of HEAD is code this
    branch actually carries.
    """
    try:
        result = subprocess.run(
            [
                "git",
                "-C",
                str(repo_root),
                "merge-base",
                "--is-ancestor",
                commit_hash,
                "HEAD",
            ],
            capture_output=True,
            timeout=30,
        )
    except (OSError, subprocess.TimeoutExpired):
        return False
    return result.returncode == 0


def _load_manifest(root: Path) -> RunProvenanceManifest | None:
    manifest_path = root / PROVENANCE_MANIFEST_PATH
    if not manifest_path.is_file():
        return None
    try:
        return RunProvenanceManifest.model_validate_json(
            manifest_path.read_text(encoding="utf-8")
        )
    except (OSError, ValidationError, ValueError) as e:
        logger.warning(f"Unreadable {PROVENANCE_MANIFEST_PATH}: {e}")
        return None


def _unavailable(detail: str) -> ProvenanceCheckResult:
    return ProvenanceCheckResult(source=SOURCE, status="unavailable", detail=detail)


class SeyvalProvenanceVerifier:
    def __init__(self, seyval_client: SeyvalClient) -> None:
        self.seyval_client = seyval_client

    async def verify(
        self, local_repo_path: str, used_dirs: set[str]
    ) -> ProvenanceCheckResult:
        root = Path(local_repo_path).expanduser().resolve()

        manifest = _load_manifest(root)
        if manifest is None:
            # Without a declaration there is nothing to pin the data to —
            # however the files got here, their provenance is unknown.
            return ProvenanceCheckResult(
                source=SOURCE,
                status="mismatch",
                checks=[
                    ProvenanceDirCheck(
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

        remote_url = _local_remote_url(root)
        if not remote_url:
            return _unavailable(
                "local clone has no 'origin' remote to match against Seyval"
            )
        normalized = _normalize_git_url(remote_url)

        try:
            repositories = await self.seyval_client.alist_repositories()
        except Exception as e:  # network / auth — degrade explicitly
            return _unavailable(f"could not list Seyval repositories: {e}")

        repo_ids = [
            r["id"]
            for r in repositories
            if _normalize_git_url(str(r.get("git_url", ""))) == normalized
        ]
        if not repo_ids:
            return _unavailable(f"no Seyval repository registered for {normalized}")

        # The repository's own run listing is the only source consulted, so
        # a declared run is accepted only if this repository actually ran it.
        listed_runs: list[dict[str, Any]] = []
        try:
            for repo_id in repo_ids:
                listed_runs.extend(await self.seyval_client.alist_runs(repo_id))
        except Exception as e:
            return _unavailable(f"could not list Seyval runs: {e}")

        # Several directories usually declare the same run (each run dir
        # plus comparison/), so its outputs listing is fetched once. The
        # dirs are checked sequentially: their count is small, and the
        # bulk of the wall clock is the per-run download, deduplicated by
        # this cache rather than by concurrency.
        outputs_cache: dict[str, dict[str, Any]] = {}
        checks = [
            await self._check_dir(root, dir_name, manifest, listed_runs, outputs_cache)
            for dir_name in sorted(used_dirs)
        ]

        all_matched = all(c.matched for c in checks)
        failed = [c.dir for c in checks if not c.matched]
        return ProvenanceCheckResult(
            source=SOURCE,
            status="verified" if all_matched else "mismatch",
            checks=checks,
            detail=(
                "" if all_matched else f"unbacked directories: {', '.join(failed)}"
            ),
        )

    async def _check_dir(
        self,
        root: Path,
        dir_name: str,
        manifest: RunProvenanceManifest,
        listed_runs: list[dict[str, Any]],
        outputs_cache: dict[str, dict[str, Any]],
    ) -> ProvenanceDirCheck:
        def fail(detail: str, **fields: Any) -> ProvenanceDirCheck:
            return ProvenanceDirCheck(
                dir=dir_name, matched=False, detail=detail, **fields
            )

        declared = manifest.dirs.get(dir_name)
        if declared is None:
            return fail(
                f"{PROVENANCE_MANIFEST_PATH} declares no run for this directory"
            )
        execution_id = declared.execution_id

        repo_path = metrics_repo_path(dir_name)
        local_file = root / repo_path
        if not local_file.is_file():
            return fail(f"local file missing: {repo_path}", run_id=execution_id)

        local_bytes = local_file.read_bytes()

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

        listing = outputs_cache.get(execution_id)
        if listing is None:
            try:
                listing = await self.seyval_client.aget_run_outputs(execution_id)
            except Exception as e:
                return fail(f"could not list run outputs: {e}", run_id=execution_id)
            outputs_cache[execution_id] = listing
        entry = next(
            (
                item
                for item in listing.get("outputs") or []
                if item.get("path") == repo_path
            ),
            None,
        )
        if entry is None:
            return fail(
                f"declared run {execution_id} did not produce {repo_path}",
                run_id=execution_id,
            )
        try:
            remote_bytes = await self.seyval_client.adownload(entry["download_url"])
        except Exception as e:
            return fail(f"could not download stored output: {e}", run_id=execution_id)

        commit_hash = str(run.get("commit_hash") or "")
        sibling_run_ids = [
            str(r.get("run_id", ""))
            for r in listed_runs
            if r.get("status") == COMPLETED_STATUS
            and str(r.get("run_id", "")) != execution_id
            and commit_hash
            and str(r.get("commit_hash") or "") == commit_hash
        ]

        if remote_bytes != local_bytes:
            return fail(
                f"local {repo_path} differs from the bytes the declared "
                f"run {execution_id} actually produced",
                run_id=execution_id,
                commit_hash=commit_hash or None,
                sibling_run_ids=sibling_run_ids,
            )

        commit_ok = bool(commit_hash) and _commit_is_ancestor(root, commit_hash)
        return ProvenanceDirCheck(
            dir=dir_name,
            run_id=execution_id,
            commit_hash=commit_hash or None,
            commit_in_history=commit_ok,
            matched=commit_ok,
            sibling_run_ids=sibling_run_ids,
            detail=(
                "byte-identical to the declared run's stored output"
                if commit_ok
                else (
                    f"bytes match run {execution_id}, but its commit "
                    f"{commit_hash[:12] or '<missing>'} is not an ancestor of "
                    "the local HEAD"
                )
            ),
        )
