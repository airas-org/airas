from logging import getLogger

from airas.core.types.github import GitHubConfig
from airas.infra.github_client import GithubClient

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
