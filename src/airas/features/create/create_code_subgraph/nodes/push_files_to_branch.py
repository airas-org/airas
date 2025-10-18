import logging

from airas.services.api_client.github_client import GithubClient
from airas.types.github import GitHubRepositoryInfo
from airas.types.research_hypothesis import ResearchHypothesis

logger = logging.getLogger(__name__)


def push_files_to_branch(
    github_repository_info: GitHubRepositoryInfo,
    new_method: ResearchHypothesis,
    commit_message: str,
    github_client: GithubClient | None = None,
) -> ResearchHypothesis:
    github_client = github_client or GithubClient()

    if (
        not new_method.experimental_design
        or not new_method.experimental_design.experiment_code
    ):
        logger.error("No experiment code found in experimental design")
        return new_method

    experiment_code = new_method.experimental_design.experiment_code
    files = experiment_code.to_file_dict(experiment_runs=new_method.experiment_runs)

    logger.info(
        f"Pushing {len(files)} files to branch {github_repository_info.branch_name}"
    )

    try:
        success = github_client.commit_multiple_files(
            github_owner=github_repository_info.github_owner,
            repository_name=github_repository_info.repository_name,
            branch_name=github_repository_info.branch_name,
            files=files,
            commit_message=commit_message,
        )

        if success:
            logger.info(
                f"Successfully pushed files to branch {github_repository_info.branch_name}"
            )
        else:
            logger.error(
                f"Failed to push files to branch {github_repository_info.branch_name}"
            )

    except Exception as e:
        logger.error(f"Error pushing files to branch: {e}")
        raise

    return new_method
