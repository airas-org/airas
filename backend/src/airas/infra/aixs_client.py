import os
from logging import getLogger
from typing import Any

import httpx

from airas.infra.base_http_client import BaseHTTPClient
from airas.infra.response_parser import ResponseParser
from airas.infra.retry_policy import make_retry_policy, raise_for_status

logger = getLogger(__name__)

AIXS_RETRY = make_retry_policy()

DEFAULT_AIXS_BASE_URL = "https://api.aixs.dev"


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
        self, repository_id: str, commit_hash: str, branch: str | None = None
    ) -> dict[str, Any]:
        """Create an analysis record for a commit (required before starting runs)."""
        path = f"v1/repositories/{repository_id}/analysis/{commit_hash}"
        resp = await self.apost(
            path=path,
            json={"branch": branch} if branch else {},
            timeout=30.0,
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
    ) -> dict[str, Any]:
        """Start a code-execution run. Not retried: a duplicate submission
        would double the compute cost."""
        path = f"v1/repositories/{repository_id}/{commit_hash}/runs"
        body: dict[str, Any] = {
            "analyzed_experiment": analyzed_experiment,
            "compute_type": compute_type,
        }
        if compute_id is not None:
            body["compute_id"] = compute_id
        if analysis_id is not None:
            body["analysis_id"] = analysis_id
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
