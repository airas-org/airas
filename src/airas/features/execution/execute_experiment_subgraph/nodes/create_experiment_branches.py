import asyncio
import logging

from dependency_injector.wiring import Provide, inject

from airas.services.api_client.api_clients_container import SyncContainer
from airas.services.api_client.github_client import GithubClient
from airas.types.github import GitHubRepositoryInfo
from airas.types.research_iteration import ExperimentRun
from airas.types.research_session import ResearchSession

logger = logging.getLogger(__name__)


async def _create_experiment_branches(
    github_client: GithubClient,
    github_repository_info: GitHubRepositoryInfo,
    experiment_runs: list[ExperimentRun],
) -> list[tuple[str, bool]]:
    base_branch_info = await github_client.aget_branch(
        github_repository_info.github_owner,
        github_repository_info.repository_name,
        github_repository_info.branch_name,
    )
    if not base_branch_info:
        raise ValueError(f"Base branch {github_repository_info.branch_name} not found")

    base_commit_sha = base_branch_info["commit"]["sha"]

    tasks = []
    branches_to_create = []

    if not experiment_runs:
        logger.warning("No experiment runs found")
        return []

    for exp_run in experiment_runs:
        child_branch = exp_run.get_branch_name(github_repository_info.branch_name)
        branches_to_create.append(child_branch)

        task = _create_single_branch(
            github_client=github_client,
            github_repository_info=github_repository_info,
            child_branch=child_branch,
            base_commit_sha=base_commit_sha,
        )
        tasks.append(task)

    success_results = await asyncio.gather(*tasks)
    return list(zip(branches_to_create, success_results, strict=True))


async def _create_single_branch(
    github_client: GithubClient,
    github_repository_info: GitHubRepositoryInfo,
    child_branch: str,
    base_commit_sha: str,
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

        logger.info(f"Successfully created branch: {child_branch}")
        return True

    except Exception as e:
        logger.error(f"Failed to create branch {child_branch}: {e}")
        return False


@inject
async def create_experiment_branches(
    github_repository_info: GitHubRepositoryInfo,
    research_session: ResearchSession,
    github_client: GithubClient = Provide[SyncContainer.github_client],
) -> ResearchSession:
    if (
        not research_session.current_iteration
        or not research_session.current_iteration.experiment_runs
    ):
        logger.error("No experiment runs found in current_iteration")
        return research_session

    branch_results = await _create_experiment_branches(
        github_client,
        github_repository_info,
        research_session.current_iteration.experiment_runs,
    )

    created_count = 0
    for exp_run in research_session.current_iteration.experiment_runs:
        child_branch = exp_run.get_branch_name(github_repository_info.branch_name)

        branch_success = next(
            (success for branch, success in branch_results if branch == child_branch),
            False,
        )

        if branch_success:
            exp_run.github_repository_info = GitHubRepositoryInfo(
                github_owner=github_repository_info.github_owner,
                repository_name=github_repository_info.repository_name,
                branch_name=child_branch,
            )
            created_count += 1
            logger.info(f"Branch {child_branch} assigned to run {exp_run.run_id}")
        else:
            logger.warning(f"Branch creation failed for run {exp_run.run_id}")

    logger.info(
        f"Successfully created {created_count} branches out of {len(research_session.current_iteration.experiment_runs)} experiment runs"
    )

    return research_session
