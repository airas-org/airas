import logging

from airas.services.api_client.github_client import GithubClient
from airas.types.github import GitHubRepositoryInfo
from airas.types.research_session import ResearchSession

logger = logging.getLogger(__name__)


def push_files_to_branch(
    github_repository_info: GitHubRepositoryInfo,
    research_session: ResearchSession,
    commit_message: str,
    github_client: GithubClient,
) -> bool:
    if not (current_iteration := research_session.current_iteration):
        logger.error("No current iteration found")
        return False

    experimental_design = current_iteration.experimental_design
    if not experimental_design or not experimental_design.experiment_code:
        logger.error("No experiment code found in experimental design")
        return False

    experiment_code = experimental_design.experiment_code
    files = experiment_code.to_file_dict(
        experiment_runs=current_iteration.experiment_runs
    )
    branch_name = github_repository_info.branch_name
    logger.info(f"Pushing {len(files)} files to branch {branch_name}")

    try:
        success = github_client.commit_multiple_files(
            github_owner=github_repository_info.github_owner,
            repository_name=github_repository_info.repository_name,
            branch_name=branch_name,
            files=files,
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
