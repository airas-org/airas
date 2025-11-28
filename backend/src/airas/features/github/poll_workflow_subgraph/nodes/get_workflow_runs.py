from logging import getLogger

from airas.services.api_client.github_client import GithubClient
from airas.types.github import GitHubConfig

logger = getLogger(__name__)


async def get_workflow_runs(
    github_config: GitHubConfig,
    github_client: GithubClient,
) -> dict | None:
    try:
        response = await github_client.alist_workflow_runs(
            github_config.github_owner,
            github_config.repository_name,
            github_config.branch_name,
        )
        return response if response else None
    except Exception as e:
        logger.warning(f"Error getting workflow runs: {e}")
        return None
