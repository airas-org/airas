import asyncio
import atexit
import os
from logging import getLogger
from typing import Any

import httpx

from airas.infra.base_http_client import BaseHTTPClient
from airas.infra.response_parser import ResponseParser
from airas.infra.retry_policy import make_retry_policy, raise_for_status

logger = getLogger(__name__)

SEYVAL_RETRY = make_retry_policy()

# Seyval deploys `main` to production and `develop` to the dev environment
# (api.dev.seyval.dev), which SEYVAL_BASE_URL can point at to try endpoints
# that have not been released to main yet.
DEFAULT_SEYVAL_BASE_URL = "https://api.seyval.dev"


class SeyvalClient(BaseHTTPClient):
    """Client for the Seyval agent compute platform.

    Seyval executes code from a registered GitHub repository on managed or
    BYO compute. The ownership chain is repository -> commit -> run: a repo
    is registered once (cloned server-side), `pull` refreshes it and lists
    branches with commit hashes, an analysis record ties a commit to runs,
    and a run executes one entry command. Auth is a Bearer `seyval_pat_` key.
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
        key = api_key or os.getenv("SEYVAL_API_KEY", "")
        super().__init__(
            base_url=(
                base_url or os.getenv("SEYVAL_BASE_URL") or DEFAULT_SEYVAL_BASE_URL
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

    @SEYVAL_RETRY
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

    @SEYVAL_RETRY
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

    @SEYVAL_RETRY
    async def aget_byo_compute_status(
        self, compute_id: str, refresh: bool = False
    ) -> dict[str, Any]:
        """Observe a registered cluster's node congestion and storage usage.

        Indicative only — for the authoritative "would a job start now?"
        answer, ask the cluster's own scheduler through Seyval's availability
        check. Partial failures are not errors: whatever could not be read
        is explained in `warnings`.

        Results are cached server-side; `refresh=True` requests a fresh
        observation but is rate-limited to protect the cluster's login node,
        and `cached` in the response says which you got.
        """
        if not compute_id.startswith("byo:"):
            raise ValueError('compute_id must start with "byo:" (e.g. "byo:<uuid>")')
        byo_uuid = compute_id.removeprefix("byo:")

        if not byo_uuid or "/" in byo_uuid:
            raise ValueError(f"Invalid BYO compute_id: {compute_id!r}")

        path = f"v1/byo-computes/{byo_uuid}/credential/status"
        resp = await self.aget(
            path=path,
            params={"refresh": "true"} if refresh else None,
            timeout=120.0,
        )
        raise_for_status(resp, path=path)
        return self._parser.parse(resp, as_="json")

    # --- runs ---

    @SEYVAL_RETRY
    async def alist_runs(self, repository_id: str) -> list[dict[str, Any]]:
        """List a repository's runs, newest first.

        Each entry carries `run_id`, `experiment_id` and `status`, which is
        what a caller needs to find the run that produced a given
        experiment's outputs. Seyval caps the list, so runs that have aged out
        can only be addressed by their id directly.
        """
        path = f"v1/repositories/{repository_id}/runs"
        resp = await self.aget(path=path, timeout=60.0)
        raise_for_status(resp, path=path)
        return self._parser.parse(resp, as_="json")

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
        # Seyval rejects an empty list, and "no inputs" is expressed by
        # omitting the field entirely.
        if inputs_from_runs:
            body["inputs_from_runs"] = inputs_from_runs
        if (time_limit is not None or resource_count is not None) and not (
            compute_id and compute_id.startswith("byo:")
        ):
            raise ValueError(
                'time_limit/resource_count require compute_id="byo:<uuid>"'
            )

        if time_limit is not None:
            body["time_limit"] = time_limit
        if resource_count is not None:
            body["resource_count"] = resource_count

        resp = await self.apost(path=path, json=body, timeout=60.0)
        raise_for_status(resp, path=path)
        return self._parser.parse(resp, as_="json")

    @SEYVAL_RETRY
    async def aget_run(self, run_id: str) -> dict[str, Any]:
        path = f"v1/runs/{run_id}"
        resp = await self.aget(path=path, timeout=30.0)
        raise_for_status(resp, path=path)
        return self._parser.parse(resp, as_="json")

    @SEYVAL_RETRY
    async def aget_run_outputs(self, run_id: str) -> dict[str, Any]:
        """Get a run's output files, each with a ready-to-use `download_url`.

        Paths are relative to the run's working directory, so an experiment
        following the airas-template contract exposes its results under
        `.research/results`. `truncated` is true when the run wrote more
        files than Seyval lists. Available wherever the run executed.
        """
        path = f"v1/runs/{run_id}/outputs"
        resp = await self.aget(path=path, timeout=60.0)
        raise_for_status(resp, path=path)
        return self._parser.parse(resp, as_="json")

    @SEYVAL_RETRY
    async def adownload(self, url: str) -> bytes:
        """Download a URL handed out by Seyval: an output file's `download_url`,
        or the `stdout_url` / `stderr_url` of a finished run.

        These URLs are pre-authorized and expire, so the API key is
        deliberately not attached. Fetch them soon after receiving them.
        """
        resp = await self.async_session.get(url, timeout=120.0, follow_redirects=True)
        raise_for_status(resp, path=url.split("?", 1)[0])
        return resp.content

    # Seyval has these two endpoints slated for removal in favour of the
    # `stdout_url` / `stderr_url` it returns for a finished run. They stay
    # because they also serve runs that have no such URL yet.
    @SEYVAL_RETRY
    async def aget_run_stdout(self, run_id: str) -> str:
        path = f"v1/runs/{run_id}/stdout"
        resp = await self.aget(path=path, timeout=60.0)
        raise_for_status(resp, path=path)
        return resp.text

    @SEYVAL_RETRY
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


_default_client: SeyvalClient | None = None


def default_seyval_client() -> SeyvalClient:
    """A lazily created process-wide client, closed at interpreter exit."""
    global _default_client
    if _default_client is None:
        _default_client = SeyvalClient(
            async_session=httpx.AsyncClient(timeout=60.0, follow_redirects=True)
        )
        atexit.register(_close_default_client)
    return _default_client


def _close_default_client() -> None:
    # atexit runs after every event loop is gone, so a fresh one is fine.
    if _default_client is not None:
        try:
            asyncio.run(_default_client.aclose())
        except Exception:  # pragma: no cover - best-effort cleanup
            pass


# ------------------------------- what a run was dispatched with, per Seyval
def parse_overrides(command_args: Any) -> dict[str, str]:
    """The dispatch's parameter overrides, from the argv Seyval recorded.

    Only `key=value` tokens are overrides; the rest of the argv is the
    interpreter and module path. Hydra's `+key=` / `~key=` prefixes are
    stripped so a declaration can be compared against what ran without
    knowing which form the dispatch used.
    """
    overrides: dict[str, str] = {}
    for token in command_args or []:
        text = str(token)
        key, separator, value = text.partition("=")
        if not separator or key.startswith("-") or "/" in key:
            continue
        overrides[key.strip().lstrip("+~")] = value.strip()
    return overrides


def parse_parameters(run: Any) -> dict[str, str]:
    """Every parameter the run resolved, as Seyval reports it.

    Strictly better than the argv-derived overrides: those carry only what
    the dispatch restated, so a parameter left at its default is
    indistinguishable from one that was never reported. Absent until the
    platform supplies it, in which case callers fall back to the overrides
    and treat a missing key as unknown rather than as a default.
    """
    reported = run.get("resolved_parameters") or run.get("parameters")
    if isinstance(reported, dict):
        return {str(k): str(v) for k, v in reported.items()}
    # The list form the run schema uses: [{"name": ..., "value": ...}, ...]
    if isinstance(reported, list):
        return {
            str(entry["name"]): str(entry.get("value"))
            for entry in reported
            if isinstance(entry, dict) and entry.get("name")
        }
    return {}
