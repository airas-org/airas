import os
from logging import getLogger
from typing import Any

import httpx

from airas.infra.base_http_client import BaseHTTPClient
from airas.infra.response_parser import ResponseParser
from airas.infra.retry_policy import make_retry_policy, raise_for_status

logger = getLogger(__name__)

AIXS_RETRY = make_retry_policy()

# AIXS deploys `develop` to the dev environment and `main` to production
# (api.airas.io). The endpoints this client uses are only on the dev
# deployment until AIXS releases them to main.
# TODO(aixs-prod): switch to "https://api.airas.io" once AIXS main ships them.
DEFAULT_AIXS_BASE_URL = "https://api.dev.airas.io"


class AixsClient(BaseHTTPClient):
    """Client for the AIXS agent compute platform.

    AIXS executes code from a registered GitHub repository on managed or
    BYO compute. The ownership chain is repository -> commit -> run: a repo
    is registered once (cloned server-side), `pull` refreshes it and lists
    branches with commit hashes, an analysis record ties a commit to runs,
    and a run executes one entry command. Auth is a Bearer `aixs_pat_` key.
    """

    def __init__(
        self,
        *,
        api_key: str | None = None,
        base_url: str | None = None,
        parser: ResponseParser | None = None,
        sync_session: httpx.Client | None = None,
        async_session: httpx.AsyncClient | None = None,
    ):
        key = api_key or os.getenv("AIXS_API_KEY", "")
        super().__init__(
            base_url=(
                base_url or os.getenv("AIXS_BASE_URL") or DEFAULT_AIXS_BASE_URL
            ).rstrip("/"),
            default_headers={"Authorization": f"Bearer {key}"} if key else {},
            sync_session=sync_session,
            async_session=async_session,
        )
        self._parser = parser or ResponseParser()

    # --- repositories ---

    async def aregister_repository(self, git_url: str) -> dict[str, Any]:
        """Register a repository (idempotent: an existing one is returned).

        Cloning happens server-side, so allow a generous timeout.
        """
        path = "v1/repositories"
        resp = await self.apost(path=path, json={"git_url": git_url}, timeout=180.0)
        raise_for_status(resp, path=path)
        return self._parser.parse(resp, as_="json")

    @AIXS_RETRY
    async def alist_repositories(self) -> list[dict[str, Any]]:
        path = "v1/repositories"
        resp = await self.aget(path=path, timeout=30.0)
        raise_for_status(resp, path=path)
        return self._parser.parse(resp, as_="json")

    async def apull_repository(self, repository_id: str) -> dict[str, Any]:
        """Refresh the server-side clone and return branches with commit hashes."""
        path = f"v1/repositories/{repository_id}/pull"
        resp = await self.apost(path=path, timeout=180.0)
        raise_for_status(resp, path=path)
        return self._parser.parse(resp, as_="json")

    # --- analyses ---

    async def astart_analysis(
        self, repository_id: str, commit_hash: str, branch: str
    ) -> dict[str, Any]:
        """Create an analysis record for a commit (required before starting runs).

        The response carries no record id, so pin a run to this analysis by
        resolving the id with `alist_analyses`.
        """
        path = f"v1/repositories/{repository_id}/analysis/{commit_hash}"
        resp = await self.apost(path=path, json={"branch": branch}, timeout=30.0)
        raise_for_status(resp, path=path)
        return self._parser.parse(resp, as_="json")

    @AIXS_RETRY
    async def alist_analyses(
        self, repository_id: str, branch: str | None = None
    ) -> list[dict[str, Any]]:
        """List analysis records, newest first. Each entry has an `analysis_id`."""
        path = f"v1/repositories/{repository_id}/analysis"
        resp = await self.aget(
            path=path,
            params={"branch": branch} if branch else None,
            timeout=30.0,
        )
        raise_for_status(resp, path=path)
        return self._parser.parse(resp, as_="json")

    # --- computes ---

    @AIXS_RETRY
    async def aget_byo_compute_status(
        self, compute_id: str, refresh: bool = False
    ) -> dict[str, Any]:
        """Observe a registered cluster's node congestion and storage usage.

        Indicative only — for the authoritative "would a job start now?"
        answer, ask the cluster's own scheduler through AIXS's availability
        check. Partial failures are not errors: whatever could not be read
        is explained in `warnings`.

        Results are cached server-side; `refresh=True` requests a fresh
        observation but is rate-limited to protect the cluster's login node,
        and `cached` in the response says which you got.
        """
        byo_uuid = compute_id.removeprefix("byo:")
        path = f"v1/byo-computes/{byo_uuid}/credential/status"
        resp = await self.aget(
            path=path,
            params={"refresh": "true"} if refresh else None,
            timeout=120.0,
        )
        raise_for_status(resp, path=path)
        return self._parser.parse(resp, as_="json")

    # --- runs ---

    async def astart_run(
        self,
        repository_id: str,
        commit_hash: str,
        analyzed_experiment: dict[str, Any],
        compute_type: str = "cpu-general",
        compute_id: str | None = None,
        analysis_id: str | None = None,
        inputs_from_runs: list[str] | None = None,
        time_limit: str | None = None,
        resource_count: int | None = None,
    ) -> dict[str, Any]:
        """Start a code-execution run. Not retried: a duplicate submission
        would double the compute cost.

        `compute_id` selects the machine (`"byo:<uuid>"` for a registered
        cluster); `compute_type` still applies on top of it, because a
        registered cluster resolves it to the resources the job asks for.

        `inputs_from_runs` restores earlier runs' outputs into this run's
        working directory at their original relative paths, so a run can
        read what a previous one wrote (measurement run -> visualization
        run, or comparing several runs). Only completed runs of the same
        repository qualify; on a path collision the last id listed wins.

        `time_limit` (e.g. "24:00:00") and `resource_count` are per-run
        requests honoured by registered clusters — the accepted values come
        from that cluster's `run_profile` in the compute catalog. Managed
        compute takes neither, since `compute_type` fixes its shape.
        """
        path = f"v1/repositories/{repository_id}/{commit_hash}/runs"
        body: dict[str, Any] = {
            "analyzed_experiment": analyzed_experiment,
            "compute_type": compute_type,
        }
        if compute_id is not None:
            body["compute_id"] = compute_id
        if analysis_id is not None:
            body["analysis_id"] = analysis_id
        # AIXS rejects an empty list, and "no inputs" is expressed by
        # omitting the field entirely.
        if inputs_from_runs:
            body["inputs_from_runs"] = inputs_from_runs
        if time_limit is not None:
            body["time_limit"] = time_limit
        if resource_count is not None:
            body["resource_count"] = resource_count
        resp = await self.apost(path=path, json=body, timeout=60.0)
        raise_for_status(resp, path=path)
        return self._parser.parse(resp, as_="json")

    @AIXS_RETRY
    async def aget_run(self, run_id: str) -> dict[str, Any]:
        path = f"v1/runs/{run_id}"
        resp = await self.aget(path=path, timeout=30.0)
        raise_for_status(resp, path=path)
        return self._parser.parse(resp, as_="json")

    @AIXS_RETRY
    async def aget_run_outputs(self, run_id: str) -> dict[str, Any]:
        """Get a run's output files, each with a ready-to-use `download_url`.

        Paths are relative to the run's working directory, so an experiment
        following the airas-template contract exposes its results under
        `.research/results`. `truncated` is true when the run wrote more
        files than AIXS lists. Available wherever the run executed.
        """
        path = f"v1/runs/{run_id}/outputs"
        resp = await self.aget(path=path, timeout=60.0)
        raise_for_status(resp, path=path)
        return self._parser.parse(resp, as_="json")

    @AIXS_RETRY
    async def adownload(self, url: str) -> bytes:
        """Download a URL handed out by AIXS: an output file's `download_url`,
        or the `stdout_url` / `stderr_url` of a finished run.

        These URLs are pre-authorized and expire, so the API key is
        deliberately not attached. Fetch them soon after receiving them.
        """
        resp = await self.async_session.get(url, timeout=120.0, follow_redirects=True)
        raise_for_status(resp, path=url.split("?", 1)[0])
        return resp.content

    # AIXS has these two endpoints slated for removal in favour of the
    # `stdout_url` / `stderr_url` it returns for a finished run. They stay
    # because they also serve runs that have no such URL yet.
    @AIXS_RETRY
    async def aget_run_stdout(self, run_id: str) -> str:
        path = f"v1/runs/{run_id}/stdout"
        resp = await self.aget(path=path, timeout=60.0)
        raise_for_status(resp, path=path)
        return resp.text

    @AIXS_RETRY
    async def aget_run_stderr(self, run_id: str) -> str:
        path = f"v1/runs/{run_id}/stderr"
        resp = await self.aget(path=path, timeout=60.0)
        raise_for_status(resp, path=path)
        return resp.text

    async def acancel_run(self, run_id: str) -> dict[str, Any]:
        path = f"v1/runs/{run_id}/cancel"
        resp = await self.apost(path=path, timeout=30.0)
        raise_for_status(resp, path=path)
        return self._parser.parse(resp, as_="json")
