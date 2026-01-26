from logging import getLogger
from typing import Any

from airas.infra.github_client import GithubClient

logger = getLogger(__name__)


async def dispatch_workflow(
    github_client: GithubClient,
    github_owner: str,
    repository_name: str,
    branch_name: str,
    workflow_file: str,
    inputs: dict[str, Any],
) -> bool:
    try:
        success = await github_client.acreate_workflow_dispatch(
            github_owner,
            repository_name,
            workflow_file,
            ref=branch_name,
            inputs=inputs,
        )
        if success:
            logger.info(
                f"Workflow dispatch sent successfully: {workflow_file} on {branch_name}"
            )
            print(
                f"Check running workflows: https://github.com/{github_owner}/{repository_name}/actions"
            )
            return True
        else:
            logger.error(f"Workflow dispatch failed: {workflow_file}")
            return False
    except Exception as e:
        logger.error(f"Failed to dispatch workflow: {e}")
        return False
