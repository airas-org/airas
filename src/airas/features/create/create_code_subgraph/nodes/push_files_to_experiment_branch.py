import asyncio
import logging

from airas.services.api_client.github_client import GithubClient
from airas.types.github import GitHubRepositoryInfo
from airas.types.research_hypothesis import (
    Experiment,
    ExperimentRun,
    ResearchHypothesis,
)

logger = logging.getLogger(__name__)


async def _push_experiments(
    github_client: GithubClient,
    github_repository_info: GitHubRepositoryInfo,
    new_method: ResearchHypothesis,
    commit_message: str,
    target_run_ids: list[tuple[str, str]],
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
    for exp_id, param_id in target_run_ids:
        child_branch = f"{github_repository_info.branch_name}-{exp_id}-{param_id}"
        branches_to_push.append(child_branch)

        # TODO: In the future, get code from experiment.runs[].code instead of experiment_code
        files = new_method.experimental_design.experiment_code.to_file_dict()

        task = _push_single_experiment(
            github_client=github_client,
            github_repository_info=github_repository_info,
            child_branch=child_branch,
            base_commit_sha=base_commit_sha,
            files=files,
            commit_message=f"{commit_message} ({exp_id}-{param_id})",
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

    # TODO: This entire block is a temporary measure for initialization and should be
    # removed once the upstream subgraphs are implemented to populate these objects.
    exp_id, param_id = "exp-1", "param-1"
    new_method.experimental_design.experiments = []
    experiment = Experiment(
        experiment_id=exp_id, description=f"Description for {exp_id}", runs=[]
    )
    experiment.runs.append(
        ExperimentRun(
            parameter_id=param_id, description=f"Description for parameters {param_id}"
        )
    )
    new_method.experimental_design.experiments.append(experiment)

    target_run_ids = [
        (experiment.experiment_id, run.parameter_id)
        for experiment in new_method.experimental_design.experiments
        for run in experiment.runs
        if run.github_repository_info is None
    ]

    if not target_run_ids:
        logger.info(
            "No new runs to push. All runs already have GitHub repository info."
        )
        return [], new_method

    push_results = asyncio.run(
        _push_experiments(
            github_client,
            github_repository_info,
            new_method,
            commit_message,
            target_run_ids,
        )
    )

    pushed_branches = []
    for (exp_id, param_id), (branch_name, success) in zip(
        target_run_ids, push_results, strict=True
    ):
        if not success:
            continue
        experiment = new_method.experimental_design.get_experiment_by_id(exp_id)
        run = experiment.get_run_by_id(param_id)
        run.github_repository_info = GitHubRepositoryInfo(
            github_owner=github_repository_info.github_owner,
            repository_name=github_repository_info.repository_name,
            branch_name=branch_name,
        )
        pushed_branches.append(branch_name)

    return pushed_branches, new_method
