import logging

from airas.core.types.github import GitHubConfig
from airas.infra.github_client import GithubClient

logger = logging.getLogger(__name__)


def push_files_to_github(
    github_config: GitHubConfig,
    push_files: dict[str, str],
    commit_message: str,
    github_client: GithubClient,
) -> bool:
    branch_name = github_config.branch_name
    logger.info(f"Pushing {len(push_files)} files to branch {branch_name}")

    try:
        success = github_client.commit_multiple_files(
            github_owner=github_config.github_owner,
            repository_name=github_config.repository_name,
            branch_name=branch_name,
            files=push_files,
            commit_message=commit_message,
        )
    except Exception as e:
        logger.exception(f"Error pushing files to branch {branch_name}: {e}")
        return False

    if not success:
        logger.error(f"Failed to push files to branch {branch_name}")
        return False

    logger.info(f"Successfully pushed files to branch {branch_name}")
    return True
