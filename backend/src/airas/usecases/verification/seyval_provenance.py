from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

from pydantic import ValidationError

from airas.core.types.paper_values import ProvenanceCheckResult, ProvenanceDirCheck
from airas.core.types.run_provenance import (
    PROVENANCE_MANIFEST_PATH,
    RunProvenanceManifest,
)
from airas.infra.local_git import (
    commit_is_ancestor,
    normalize_git_url,
    remote_origin_url,
)
from airas.infra.seyval_client import SeyvalClient
from airas.usecases.publication.paper_values.compute import RESULTS_DIR
from airas.usecases.publication.paper_values.provenance import metrics_repo_path
from airas.usecases.verification.run_parameters import (
    parse_overrides,
    parse_parameters,
)

logger = logging.getLogger(__name__)

SOURCE = "seyval"

COMPLETED_STATUS = "completed"


def load_provenance_manifest(root: Path) -> RunProvenanceManifest | None:
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

        manifest = load_provenance_manifest(root)
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

        remote_url = remote_origin_url(root)
        if not remote_url:
            return _unavailable(
                "local clone has no 'origin' remote to match against Seyval"
            )
        normalized = normalize_git_url(remote_url)

        try:
            repositories = await self.seyval_client.alist_repositories()
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
        if (
            declared.commit_hash
            and seyval_commit
            and declared.commit_hash != seyval_commit
        ):
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
        parameters_match: bool | None = None
        seyval_overrides = parse_overrides(run.get("command_args"))
        seyval_parameters = parse_parameters(run)
        if seyval_overrides or seyval_parameters:
            parameters_match = (
                not seyval_overrides or dict(declared.overrides) == seyval_overrides
            ) and (
                not seyval_parameters or dict(declared.parameters) == seyval_parameters
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
                listing = await self.seyval_client.aget_run_outputs(execution_id)
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
        local_paths = sorted(
            str(path.relative_to(root))
            for path in dir_root.rglob("*")
            if path.is_file()
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
                remote_bytes = await self.seyval_client.adownload(entry["download_url"])
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
        return ProvenanceDirCheck(
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
