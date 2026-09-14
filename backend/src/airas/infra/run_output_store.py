"""The place a backend keeps a run's outputs: what import copies from and
the record gate compares against. Dispatch differs too much per backend to
share and stays in `dispatch_experiment`.

TODO(manual / RunPod): needs a store the agent cannot rewrite.
"""

from __future__ import annotations

import io
import os
import re
import zipfile
from functools import partial
from typing import Any, Callable, Literal, Protocol

import httpx
from pydantic import BaseModel

from airas.core.research_paths import RESULTS_DIR
from airas.infra.github_client import GithubClient
from airas.infra.local_git import normalize_git_url
from airas.infra.seyval_client import (
    SeyvalClient,
    default_seyval_client,
    parse_overrides,
    parse_parameters,
)

Backend = Literal["seyval", "github_actions"]

COMPLETED_STATUS = "completed"


class StoredRun(BaseModel):
    execution_id: str
    status: str
    commit_hash: str | None = None
    # None: the backend did not report the dispatch at all.
    overrides: dict[str, str] | None = None
    parameters: dict[str, str] | None = None


class RunExpired(LookupError):
    """The backend says it dropped the outputs; an unknown run is a plain LookupError."""


class RunOutputStore(Protocol):
    backend: str

    async def alist_runs(self) -> list[StoredRun]: ...

    async def alist_outputs(self, execution_id: str) -> dict[str, int]:
        """Repository-relative POSIX path -> size in bytes."""
        ...

    async def adownload(self, execution_id: str, path: str) -> bytes: ...


class SeyvalOutputStore:
    backend = "seyval"

    def __init__(self, client: SeyvalClient, git_url: str) -> None:
        self._client = client
        self._git_url = normalize_git_url(git_url)
        self._listings: dict[str, dict[str, dict[str, Any]]] = {}

    async def alist_runs(self) -> list[StoredRun]:
        repositories = await self._client.alist_repositories()
        repo_ids = [
            r["id"]
            for r in repositories
            if normalize_git_url(str(r.get("git_url", ""))) == self._git_url
        ]
        if not repo_ids:
            raise LookupError(f"no Seyval repository registered for {self._git_url}")
        runs: list[StoredRun] = []
        for repo_id in repo_ids:
            runs += [_seyval_run(run) for run in await self._client.alist_runs(repo_id)]
        return runs

    async def alist_outputs(self, execution_id: str) -> dict[str, int]:
        listing = await self._listing(execution_id)
        return {
            path: int(item.get("size_bytes") or 0) for path, item in listing.items()
        }

    async def adownload(self, execution_id: str, path: str) -> bytes:
        item = (await self._listing(execution_id)).get(path)
        url = item.get("download_url") if item else None
        if not url:
            raise ValueError(
                f"Seyval listed {path} for run {execution_id} without a "
                "download_url, so it cannot be fetched."
            )
        return await self._client.adownload(url)

    async def _listing(self, execution_id: str) -> dict[str, dict[str, Any]]:
        cached = self._listings.get(execution_id)
        if cached is None:
            listing = await self._client.aget_run_outputs(execution_id)
            if listing.get("truncated"):
                raise ValueError(
                    f"Seyval truncated the output listing for run {execution_id}, "
                    "so an import would silently drop files. Reduce what the run "
                    "writes outside the results directory, or import the files "
                    "manually."
                )
            cached = {
                str(item["path"]): item
                for item in listing.get("outputs") or []
                if item.get("path")
            }
            self._listings[execution_id] = cached
        return cached


def _seyval_run(run: dict[str, Any]) -> StoredRun:
    reports_overrides = run.get("command_args") is not None
    reports_parameters = (
        run.get("resolved_parameters") is not None or run.get("parameters") is not None
    )
    return StoredRun(
        execution_id=str(run.get("run_id", "")),
        status=str(run.get("status") or ""),
        commit_hash=str(run.get("commit_hash") or "") or None,
        overrides=parse_overrides(run.get("command_args"))
        if reports_overrides
        else None,
        parameters=parse_parameters(run) if reports_parameters else None,
    )


# run_experiment.yml: run-name "[<mode>] <run_id>", artifact
# "<mode>-<workflow run id>-<run_id>" holding `.research/results/<run_id>/`.
_RUN_TITLE = re.compile(r"^\[(sanity|pilot|full)\] (.+)$")
_ARTIFACT_NAME = re.compile(r"^(sanity|pilot|full)-\d+-(.+)$")


class GithubActionsOutputStore:
    backend = "github_actions"

    def __init__(
        self, client: GithubClient, github_owner: str, repository_name: str
    ) -> None:
        self._client = client
        self._owner = github_owner
        self._repo = repository_name
        self._archives: dict[str, dict[str, bytes]] = {}

    async def alist_runs(self) -> list[StoredRun]:
        # ponytail: newest 100 only; add paging when an older run is still needed
        response = await self._client.alist_workflow_runs(
            self._owner, self._repo, event="workflow_dispatch", per_page=100
        )
        return [_actions_run(run) for run in (response or {}).get("workflow_runs", [])]

    async def alist_outputs(self, execution_id: str) -> dict[str, int]:
        archive = await self._archive(execution_id)
        return {path: len(content) for path, content in archive.items()}

    async def adownload(self, execution_id: str, path: str) -> bytes:
        archive = await self._archive(execution_id)
        if path not in archive:
            raise ValueError(f"workflow run {execution_id} produced no {path}")
        return archive[path]

    async def _archive(self, execution_id: str) -> dict[str, bytes]:
        cached = self._archives.get(execution_id)
        if cached is not None:
            return cached
        response = await self._client.alist_workflow_run_artifacts(
            self._owner, self._repo, int(execution_id)
        )
        matches = [
            (artifact, match)
            for artifact in (response or {}).get("artifacts", [])
            if (match := _ARTIFACT_NAME.match(str(artifact.get("name", ""))))
        ]
        if not matches:
            raise LookupError(f"workflow run {execution_id} has no results artifact")
        artifact, match = matches[0]
        if artifact.get("expired"):
            raise RunExpired(
                f"the results artifact of workflow run {execution_id} has "
                "expired (GitHub's artifact retention)"
            )
        zip_bytes = await self._client.adownload_artifact_archive(
            self._owner, self._repo, int(artifact["id"])
        )
        if not zip_bytes:
            raise LookupError(
                f"the results artifact of workflow run {execution_id} is empty"
            )
        prefix = f"{RESULTS_DIR}/{match.group(2)}/"
        with zipfile.ZipFile(io.BytesIO(zip_bytes)) as zipped:
            files = {
                prefix + info.filename: zipped.read(info)
                for info in zipped.infolist()
                if not info.is_dir()
            }
        self._archives[execution_id] = files
        return files


def _actions_run(run: dict[str, Any]) -> StoredRun:
    succeeded = run.get("status") == "completed" and run.get("conclusion") == "success"
    # The API does not expose workflow inputs; the run name carries the mode.
    title = _RUN_TITLE.match(str(run.get("display_title") or ""))
    return StoredRun(
        execution_id=str(run.get("id", "")),
        status=(
            COMPLETED_STATUS
            if succeeded
            else str(run.get("conclusion") or run.get("status") or "")
        ),
        commit_hash=str(run.get("head_sha") or "") or None,
        overrides={"mode": title.group(1)} if title else None,
    )


def build_store(
    backend: str,
    git_url: str,
    *,
    seyval_client: Callable[[], SeyvalClient],
    github_client: Callable[[], GithubClient],
) -> RunOutputStore:
    if backend == "seyval":
        return SeyvalOutputStore(seyval_client(), git_url)
    if backend == "github_actions":
        owner, repo = _owner_and_repo(git_url)
        return GithubActionsOutputStore(github_client(), owner, repo)
    raise ValueError(f"unknown execution backend {backend!r}")


def _owner_and_repo(git_url: str) -> tuple[str, str]:
    match = re.match(
        r"^https://github\.com/([^/]+)/([^/]+)$", normalize_git_url(git_url)
    )
    if match is None:
        raise ValueError(f"not a GitHub repository URL: {git_url}")
    return match.group(1), match.group(2)


def _default_github_client() -> GithubClient:
    token = os.getenv("GH_PERSONAL_ACCESS_TOKEN")
    if not token:
        raise RuntimeError("GH_PERSONAL_ACCESS_TOKEN is not set")
    return GithubClient(
        github_token=token,
        async_session=httpx.AsyncClient(timeout=60.0, follow_redirects=True),
    )


default_store: Callable[[str, str], RunOutputStore] = partial(
    build_store,
    seyval_client=default_seyval_client,
    github_client=_default_github_client,
)
