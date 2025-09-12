import logging

from airas.services.api_client.github_client import GithubClient
from airas.types.github import GitHubRepositoryInfo

logger = logging.getLogger(__name__)


def push_files_to_github(
    github_repository_info: GitHubRepositoryInfo,
    files: dict[str, str],
    commit_message: str,
    github_client: GithubClient | None = None,
) -> bool:
    github_client = github_client or GithubClient()

    success = github_client.commit_multiple_files(
        github_owner=github_repository_info.github_owner,
        repository_name=github_repository_info.repository_name,
        branch_name=github_repository_info.branch_name,
        files=files,
        commit_message=commit_message,
    )

    if success:
        logger.info(
            f"Successfully pushed files to {github_repository_info.github_owner}/{github_repository_info.repository_name} on branch {github_repository_info.branch_name}"
        )
        # created_files = list(state["generated_files"].keys()) if success else []
        return True
    else:
        logger.error(
            f"Failed to push files to {github_repository_info.github_owner}/{github_repository_info.repository_name} on branch {github_repository_info.branch_name}"
        )
        return False
