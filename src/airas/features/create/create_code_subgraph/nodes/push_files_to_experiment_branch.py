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
    target_experiment_ids: list[str],
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
    branches_to_push = []
    for exp_id in target_experiment_ids:
        child_branch = f"{github_repository_info.branch_name}-{exp_id}"
        branches_to_push.append(child_branch)

        # Get code from experiment.code
        experiment = new_method.experimental_design.get_experiment_by_id(exp_id)
        if not experiment or not experiment.code:
            logger.error(f"No code found for experiment {exp_id}")
            continue

        files = experiment.code.to_file_dict()

        task = _push_single_experiment(
            github_client=github_client,
            github_repository_info=github_repository_info,
            child_branch=child_branch,
            base_commit_sha=base_commit_sha,
            files=files,
            commit_message=f"{commit_message} ({exp_id})",
        )
        tasks.append(task)

    success_results = await asyncio.gather(*tasks)
    return list(zip(branches_to_push, success_results, strict=True))


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


def push_files_to_experiment_branch(
    github_repository_info: GitHubRepositoryInfo,
    new_method: ResearchHypothesis,
    commit_message: str,
    github_client: GithubClient | None = None,
) -> tuple[list[str], ResearchHypothesis]:
    github_client = github_client or GithubClient()

    if (
        not new_method.experimental_design
        or not new_method.experimental_design.experiments
    ):
        logger.error("No experiments found in experimental design")
        return [], new_method

    # Push only experiments that are not selected for paper (need improvement and re-execution)
    # Experiments with is_selected_for_paper=True are already successful and don't need re-execution
    target_experiment_ids = [
        experiment.experiment_id
        for experiment in new_method.experimental_design.experiments
        if not (experiment.evaluation and experiment.evaluation.is_selected_for_paper)
    ]

    if not target_experiment_ids:
        logger.info(
            "No experiments need re-execution. All experiments are already selected for paper."
        )
        return [], new_method

    push_results = asyncio.run(
        _push_experiments(
            github_client,
            github_repository_info,
            new_method,
            commit_message,
            target_experiment_ids,
        )
    )

    pushed_branches = []
    for exp_id, (branch_name, success) in zip(
        target_experiment_ids, push_results, strict=True
    ):
        if not success:
            continue
        experiment = new_method.experimental_design.get_experiment_by_id(exp_id)
        experiment.github_repository_info = GitHubRepositoryInfo(
            github_owner=github_repository_info.github_owner,
            repository_name=github_repository_info.repository_name,
            branch_name=branch_name,
        )
        pushed_branches.append(branch_name)

    return pushed_branches, new_method
