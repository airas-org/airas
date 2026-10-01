import logging
from typing import Any

from airas.core.types.execution_backend import ExecutionBackend
from airas.core.types.github import require_github_repo
from airas.infra.github_client import GithubClient
from airas.infra.retry_policy import HTTPClientFatalError, HTTPClientRetryableError
from airas.infra.seyval_client import SeyvalClient

logger = logging.getLogger(__name__)

MAX_LOG_TAIL_LINES = 10_000


async def get_experiment_run_status(
    execution_id: str,
    *,
    backend: ExecutionBackend,
    github_client: GithubClient | None = None,
    seyval_client: SeyvalClient | None = None,
    github_owner: str | None = None,
    repository_name: str | None = None,
    log_tail_lines: int = 200,
) -> dict[str, Any]:
    if log_tail_lines <= 0:
        raise ValueError("log_tail_lines must be a positive integer")
    log_tail_lines = min(log_tail_lines, MAX_LOG_TAIL_LINES)

    match backend:
        case "github_actions":
            if github_client is None:
                raise ValueError('backend="github_actions" needs a github_client')
            github_owner, repository_name = require_github_repo(
                github_owner, repository_name
            )
            run_info = await github_client.aget_workflow_run(
                github_owner=github_owner,
                repository_name=repository_name,
                workflow_run_id=int(execution_id),
            )
            if run_info is None:
                raise ValueError(
                    f"Workflow run {execution_id} not found in "
                    f"{github_owner}/{repository_name}"
                )
            return {
                "execution_id": execution_id,
                "backend": backend,
                "status": run_info.get("status"),
                "conclusion": run_info.get("conclusion"),
                "execution_url": run_info.get("html_url"),
                # Actions job logs are not exposed here; inspect the run page or
                # use download_workflow_artifacts for outputs.
                "stdout_tail": None,
                "stderr_tail": None,
            }
        case "seyval":
            if seyval_client is None:
                raise ValueError('backend="seyval" needs a seyval_client')
        case _:
            raise ValueError(f"unknown backend {backend!r}")

    run = await seyval_client.aget_run(execution_id)
    status = run.get("status")

    def _tail(text: str) -> str:
        lines = text.splitlines()
        return "\n".join(lines[-log_tail_lines:])

    stdout_tail: str | None = None
    stderr_tail: str | None = None
    if status in ("completed", "failed", "cancelled"):
        try:
            stdout_tail = _tail(await seyval_client.aget_run_stdout(execution_id))
        except (HTTPClientFatalError, HTTPClientRetryableError) as exc:
            # logs may not be persisted (yet) for this run
            logger.warning(f"Failed to fetch stdout for run {execution_id}: {exc}")
        try:
            stderr_tail = _tail(await seyval_client.aget_run_stderr(execution_id))
        except (HTTPClientFatalError, HTTPClientRetryableError) as exc:
            logger.warning(f"Failed to fetch stderr for run {execution_id}: {exc}")

    return {
        "execution_id": execution_id,
        "backend": backend,
        "status": status,
        "compute_type": run.get("compute_type"),
        "duration_seconds": run.get("duration_seconds"),
        "stdout_tail": stdout_tail,
        "stderr_tail": stderr_tail,
    }
