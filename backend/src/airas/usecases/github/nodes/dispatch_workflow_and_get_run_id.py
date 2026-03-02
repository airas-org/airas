import asyncio
import logging
from typing import Any

from airas.infra.github_client import GithubClient

logger = logging.getLogger(__name__)

_POLL_INTERVAL_SECONDS = 3
_MAX_ATTEMPTS = 20


async def dispatch_workflow_and_get_run_id(
    github_client: GithubClient,
    github_owner: str,
    repository_name: str,
    branch_name: str,
    workflow_file: str,
    inputs: dict[str, Any],
) -> int | None:
    before = await github_client.alist_workflow_runs_for_workflow(
        github_owner=github_owner,
        repository_name=repository_name,
        workflow_file_name=workflow_file,
        branch_name=branch_name,
    )
    existing_ids: set[int] = set()
    if before and "workflow_runs" in before:
        existing_ids = {run["id"] for run in before["workflow_runs"]}

    success = await github_client.acreate_workflow_dispatch(
        github_owner,
        repository_name,
        workflow_file,
        ref=branch_name,
        inputs=inputs,
    )
    if not success:
        logger.error(f"Workflow dispatch failed: {workflow_file}")
        return None

    logger.info(f"Workflow dispatch accepted: {workflow_file} on {branch_name}")

    for attempt in range(1, _MAX_ATTEMPTS + 1):
        await asyncio.sleep(_POLL_INTERVAL_SECONDS)

        after = await github_client.alist_workflow_runs_for_workflow(
            github_owner=github_owner,
            repository_name=repository_name,
            workflow_file_name=workflow_file,
            branch_name=branch_name,
        )
        if not after or "workflow_runs" not in after:
            continue

        for run in after["workflow_runs"]:
            if run["id"] not in existing_ids:
                run_id: int = run["id"]
                logger.info(f"New workflow run detected: {run_id} (attempt {attempt})")
                return run_id

        logger.info(f"No new workflow run yet (attempt {attempt}/{_MAX_ATTEMPTS})")

    logger.error(
        f"workflow_run_id not found after {_MAX_ATTEMPTS} attempts for {workflow_file}"
    )
    return None
