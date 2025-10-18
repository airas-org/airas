import asyncio
import json
from logging import getLogger
from typing import Any

from airas.config.runner_type_info import RunnerType, runner_info_dict
from airas.features.execution.execute_experiment_subgraph.workflow_executor import (
    WorkflowExecutor,
    WorkflowResult,
)
from airas.services.api_client.github_client import GithubClient
from airas.types.github import GitHubRepositoryInfo
from airas.types.research_hypothesis import ResearchHypothesis

logger = getLogger(__name__)


async def _execute_workflow_on_branch(
    executor: WorkflowExecutor,
    github_owner: str,
    repository_name: str,
    branch_name: str,
    workflow_file: str,
    inputs: dict[str, Any],
) -> WorkflowResult:
    result = await executor.execute_workflow(
        github_owner,
        repository_name,
        branch_name,
        workflow_file,
        inputs,
    )

    if result.success:
        logger.info(f"Workflow on branch '{branch_name}' completed successfully")
    else:
        logger.error(
            f"Workflow on branch '{branch_name}' failed: {result.error_message}"
        )

    return result


async def _execute_trial_experiment_async(
    github_repository: GitHubRepositoryInfo,
    experiment_iteration: int,
    runner_type: RunnerType,
    new_method: ResearchHypothesis,
    workflow_file: str,
    github_client: GithubClient | None = None,
) -> bool:
    if not new_method.experiment_runs:
        logger.error("No experiment runs found in new_method")
        return False

    client = github_client or GithubClient()
    executor = WorkflowExecutor(client)
    runner_type_setting = runner_info_dict[runner_type]["runner_setting"]

    branch_name = github_repository.branch_name
    run_ids = [run.run_id for run in new_method.experiment_runs]

    logger.info(
        f"Executing trial experiment: {len(run_ids)} run_ids on branch '{branch_name}'"
    )
    logger.info(f"Run IDs: {', '.join(run_ids)}")

    inputs = {
        "experiment_iteration": str(experiment_iteration),
        "runner_type": runner_type_setting,
        "run_ids": json.dumps(run_ids),
    }

    result = await _execute_workflow_on_branch(
        executor,
        github_repository.github_owner,
        github_repository.repository_name,
        branch_name,
        workflow_file,
        inputs,
    )

    return result.success


async def _execute_full_experiments_async(
    github_repository: GitHubRepositoryInfo,
    experiment_iteration: int,
    runner_type: RunnerType,
    new_method: ResearchHypothesis,
    workflow_file: str,
    github_client: GithubClient | None = None,
) -> bool:
    if not new_method.experiment_runs:
        logger.error("No experiment runs found in new_method")
        return False

    client = github_client or GithubClient()
    executor = WorkflowExecutor(client)
    runner_type_setting = runner_info_dict[runner_type]["runner_setting"]

    base_inputs = {
        "experiment_iteration": str(experiment_iteration),
        "runner_type": runner_type_setting,
    }

    tasks = []
    for exp_run in new_method.experiment_runs:
        if not exp_run.github_repository_info:
            logger.warning(f"No branch information for run {exp_run.run_id}, skipping")
            continue

        inputs = base_inputs.copy()
        inputs["run_id"] = exp_run.run_id

        task = _execute_workflow_on_branch(
            executor,
            github_repository.github_owner,
            github_repository.repository_name,
            exp_run.github_repository_info.branch_name,
            workflow_file,
            inputs,
        )
        tasks.append((exp_run.run_id, exp_run.github_repository_info.branch_name, task))

    if not tasks:
        logger.error("No valid experiment runs to execute")
        return False

    logger.info(
        f"Executing full experiments: {len(tasks)} run_ids across {len(tasks)} branches"
    )

    results_list = await asyncio.gather(*[task for _, _, task in tasks])

    all_success = True
    for (run_id, branch_name, _), result in zip(tasks, results_list, strict=True):
        if result.success:
            logger.info(
                f"Experiment run '{run_id}' on branch '{branch_name}' completed successfully"
            )
        else:
            logger.error(
                f"Experiment run '{run_id}' on branch '{branch_name}' failed: {result.error_message}"
            )
            all_success = False

    if all_success:
        logger.info(f"All {len(tasks)} experiment runs completed successfully")
    else:
        failed_count = sum(1 for result in results_list if not result.success)
        logger.error(f"{failed_count} out of {len(tasks)} experiments failed")

    return all_success


async def _execute_evaluation_async(
    github_repository: GitHubRepositoryInfo,
    experiment_iteration: int,
    workflow_file: str,
    github_client: GithubClient | None = None,
) -> bool:
    client = github_client or GithubClient()
    executor = WorkflowExecutor(client)

    branch_name = github_repository.branch_name

    logger.info(f"Executing evaluation on main branch '{branch_name}'")

    inputs = {
        "experiment_iteration": str(experiment_iteration),
    }

    result = await _execute_workflow_on_branch(
        executor,
        github_repository.github_owner,
        github_repository.repository_name,
        branch_name,
        workflow_file,
        inputs,
    )

    return result.success


def execute_trial_experiment(
    github_repository: GitHubRepositoryInfo,
    experiment_iteration: int,
    runner_type: RunnerType,
    new_method: ResearchHypothesis,
    workflow_file: str = "run_trial_experiment_with_open_code.yml",
    github_client: GithubClient | None = None,
) -> bool:
    return asyncio.run(
        _execute_trial_experiment_async(
            github_repository,
            experiment_iteration,
            runner_type,
            new_method,
            workflow_file,
            github_client,
        )
    )


def execute_full_experiments(
    github_repository: GitHubRepositoryInfo,
    experiment_iteration: int,
    runner_type: RunnerType,
    new_method: ResearchHypothesis,
    workflow_file: str = "run_full_experiment_with_open_code.yml",
    github_client: GithubClient | None = None,
) -> bool:
    return asyncio.run(
        _execute_full_experiments_async(
            github_repository,
            experiment_iteration,
            runner_type,
            new_method,
            workflow_file,
            github_client,
        )
    )


def execute_evaluation(
    github_repository: GitHubRepositoryInfo,
    experiment_iteration: int,
    workflow_file: str = "run_evaluation_with_open_code.yml",
    github_client: GithubClient | None = None,
) -> bool:
    return asyncio.run(
        _execute_evaluation_async(
            github_repository,
            experiment_iteration,
            workflow_file,
            github_client,
        )
    )
