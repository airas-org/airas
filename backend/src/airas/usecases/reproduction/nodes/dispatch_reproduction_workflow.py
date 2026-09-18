import json
import logging

from airas.core.types.github import GitHubConfig
from airas.infra.github.nodes.dispatch_workflow import dispatch_workflow
from airas.infra.github_client import GithubClient

logger = logging.getLogger(__name__)


async def dispatch_reproduction_workflow(
    github_client: GithubClient,
    github_config: GitHubConfig,
    workflow_file: str,
    inputs: dict[str, str],
    runner_label: list[str] | None,
) -> bool:
    runner_label = runner_label or ["ubuntu-latest"]
    logger.info(
        f"Dispatching {workflow_file} on branch '{github_config.branch_name}' "
        f"with runner_label={runner_label}"
    )
    success = await dispatch_workflow(
        github_client,
        github_config.github_owner,
        github_config.repository_name,
        github_config.branch_name,
        workflow_file,
        {
            "branch_name": github_config.branch_name,
            **inputs,
            "runner_label": json.dumps(runner_label),
        },
    )
    (logger.info if success else logger.error)(
        f"Dispatch {'successful' if success else 'failed'}: {workflow_file}"
    )
    return success
