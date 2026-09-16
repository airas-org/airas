from logging import getLogger

from airas.core.types.github import GitHubConfig
from airas.infra.github_client import GithubClient

logger = getLogger(__name__)


def check_branch_existence(
    github_config: GitHubConfig,
    github_client: GithubClient,
) -> str | None:
    response = github_client.get_branch(
        github_owner=github_config.github_owner,
        repository_name=github_config.repository_name,
        branch_name=github_config.branch_name,
    )
    if response is None:
        logger.warning(
            f"Branch '{github_config.branch_name}' not found in repository '{github_config.repository_name}'."
        )
        return None

    try:
        return response["commit"]["sha"]
    except KeyError:
        logger.warning(
            f"Unexpected response format: missing 'commit.sha'. Response: {response}"
        )
        return None
