from logging import getLogger

from airas.services.api_client.github_client import GithubClient
from airas.types.github import GitHubConfig

logger = getLogger(__name__)


async def get_baseline_workflow_count(
    github_config: GitHubConfig,
    github_client: GithubClient,
) -> int | None:
    try:
        response = await github_client.alist_workflow_runs(
            github_config.github_owner,
            github_config.repository_name,
            github_config.branch_name,
        )
        if not response:
            return None
        count = len(response.get("workflow_runs", []))
        logger.info(f"Baseline workflow count: {count}")
        return count
    except Exception as e:
        logger.error(f"Failed to get baseline workflow count: {e}")
        return None
