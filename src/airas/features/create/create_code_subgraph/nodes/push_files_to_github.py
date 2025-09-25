import asyncio
import logging

from airas.services.api_client.github_client import GithubClient
from airas.types.github import GitHubRepositoryInfo
from airas.types.research_hypothesis import ResearchHypothesis

logger = logging.getLogger(__name__)


async def _push_experiments(
    github_client: GithubClient,
    github_repository_info: GitHubRepositoryInfo,
    new_method: ResearchHypothesis,
    commit_message: str,
    experiments: list[tuple[int, int]],
) -> list[bool]:
    # First, get the base branch info to get the SHA for creating child branches
    base_branch_info = await github_client.aget_branch(
        github_repository_info.github_owner,
        github_repository_info.repository_name,
        github_repository_info.branch_name,
    )
    if not base_branch_info:
        raise ValueError(f"Base branch {github_repository_info.branch_name} not found")

    base_commit_sha = base_branch_info["commit"]["sha"]

    tasks = []
    for exp_id, var_id in experiments:
        child_branch = github_repository_info.add_child_branch(exp_id, var_id)
        files = new_method.experimental_design.experiment_code.to_file_dict()

        # Create child branch and commit files
        task = _push_single_experiment(
            github_client=github_client,
            github_repository_info=github_repository_info,
            child_branch=child_branch,
            base_commit_sha=base_commit_sha,
            files=files,
            commit_message=f"{commit_message} ({exp_id}-{var_id})",
        )
        tasks.append(task)

    return await asyncio.gather(*tasks)


async def _push_single_experiment(
    github_client: GithubClient,
    github_repository_info: GitHubRepositoryInfo,
    child_branch: str,
    base_commit_sha: str,
    files: dict[str, str],
    commit_message: str,
) -> bool:
    try:
        branch_created = await github_client.acreate_branch(
            github_owner=github_repository_info.github_owner,
            repository_name=github_repository_info.repository_name,
            branch_name=child_branch,
            from_sha=base_commit_sha,
        )

        if not branch_created:
            logger.error(f"Failed to create child branch: {child_branch}")
            return False

        commit_success = await github_client.acommit_multiple_files(
            github_owner=github_repository_info.github_owner,
            repository_name=github_repository_info.repository_name,
            branch_name=child_branch,
            files=files,
            commit_message=commit_message,
        )

        return commit_success

    except Exception as e:
        logger.error(f"Failed to push to child branch {child_branch}: {e}")
        return False


def push_files_to_github(
    github_repository_info: GitHubRepositoryInfo,
    new_method: ResearchHypothesis,
    commit_message: str,
    github_client: GithubClient | None = None,
) -> bool:
    github_client = github_client or GithubClient()

    # TODO: 将来的には複数実験に対応
    # 現在は単一実験として処理
    experiments = [(0, 0)]  # experiment_id, variation_id

    success_results = asyncio.run(
        _push_experiments(
            github_client,
            github_repository_info,
            new_method,
            commit_message,
            experiments,
        )
    )

    success = all(success_results)

    if success:
        logger.info(
            f"Successfully pushed files to {github_repository_info.github_owner}/{github_repository_info.repository_name} on branch {github_repository_info.branch_name}"
        )
        return True

    logger.error(
        f"Failed to push files to {github_repository_info.github_owner}/{github_repository_info.repository_name} on branch {github_repository_info.branch_name}"
    )
    return False
