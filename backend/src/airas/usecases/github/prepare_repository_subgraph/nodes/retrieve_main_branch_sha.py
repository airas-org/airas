from logging import getLogger

from airas.core.types.github import GitHubConfig
from airas.infra.github_client import GithubClient

logger = getLogger(__name__)


def retrieve_main_branch_sha(
    github_config: GitHubConfig,
    github_client: GithubClient,
) -> str:
    response = github_client.get_branch(
        github_owner=github_config.github_owner,
        repository_name=github_config.repository_name,
        branch_name="main",
    )

    if not response or not isinstance(response, dict):
        raise RuntimeError(
            f"Failed to retrieve branch info for 'main' branch of {github_config.github_owner}/{github_config.repository_name}"
        )

    try:
        sha = response["commit"]["sha"]
    except (TypeError, KeyError):
        msg = f"Invalid response format for 'main' branch of {github_config.github_owner}/{github_config.repository_name}"
        raise RuntimeError(msg)  # noqa: B904

    if not sha:
        raise RuntimeError(
            f"Empty SHA for 'main' branch of {github_config.github_owner}/{github_config.repository_name}"
        )
    return sha
