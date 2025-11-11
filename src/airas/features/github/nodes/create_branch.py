from logging import getLogger
from typing import Literal

from airas.services.api_client.github_client import GithubClient
from airas.types.github import GitHubRepositoryInfo

logger = getLogger(__name__)

# NOTE：API Documentation
# https://docs.github.com/ja/rest/git/refs?apiVersion=2022-11-28#create-a-reference


def create_branch(
    github_repository_info: GitHubRepositoryInfo,
    sha: str,
    github_client: GithubClient,
) -> Literal[True]:
    existing_branch = github_client.get_branch(
        github_owner=github_repository_info.github_owner,
        repository_name=github_repository_info.repository_name,
        branch_name=github_repository_info.branch_name,
    )

    if existing_branch:
        logger.info(
            f"Branch '{github_repository_info.branch_name}' already exists in repository "
            f"'{github_repository_info.github_owner}/{github_repository_info.repository_name}'. "
            f"Skipping branch creation."
        )
        return True

    try:
        response = github_client.create_branch(
            github_owner=github_repository_info.github_owner,
            repository_name=github_repository_info.repository_name,
            branch_name=github_repository_info.branch_name,
            from_sha=sha,
        )
        if response:
            logger.info(
                f"Branch '{github_repository_info.branch_name}' created in repository "
                f"'{github_repository_info.github_owner}/{github_repository_info.repository_name}'"
            )
            return True
        else:
            raise RuntimeError(
                f"Failed to create branch '{github_repository_info.branch_name}' from '{sha}' in "
                f"{github_repository_info.github_owner}/{github_repository_info.repository_name}"
            )
    except Exception as e:
        raise RuntimeError(
            f"Failed to create new branch '{github_repository_info.branch_name}' from '{sha}' in "
            f"{github_repository_info.github_owner}/{github_repository_info.repository_name}: {e}"
        ) from e
