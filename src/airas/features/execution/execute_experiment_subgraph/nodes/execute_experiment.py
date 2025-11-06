import asyncio
import json
from logging import getLogger
from typing import Any

from dependency_injector.wiring import Provide, inject

from airas.config.runner_type_info import RunnerType, runner_info_dict
from airas.features.execution.execute_experiment_subgraph.workflow_executor import (
    WorkflowExecutor,
    WorkflowResult,
)
from airas.services.api_client.api_clients_container import SyncContainer
from airas.services.api_client.github_client import GithubClient
from airas.types.github import GitHubRepositoryInfo
from airas.types.research_session import ResearchSession

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


@inject
async def execute_trial_experiment(
    github_repository: GitHubRepositoryInfo,
    experiment_iteration: int,
    runner_type: RunnerType,
    research_session: ResearchSession,
    workflow_file: str = "run_trial_experiment_with_claude_code_v2.yml",
    github_client: GithubClient = Provide[SyncContainer.github_client],
) -> bool:
    if (
        not research_session.current_iteration
        or not research_session.current_iteration.experiment_runs
    ):
        logger.error("No experiment runs found in current_iteration")
        return False

    executor = WorkflowExecutor(github_client)
    runner_type_setting = runner_info_dict[runner_type]["runner_setting"]

    branch_name = github_repository.branch_name
    run_ids = [run.run_id for run in research_session.current_iteration.experiment_runs]

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


@inject
async def execute_full_experiments(
    github_repository: GitHubRepositoryInfo,
    experiment_iteration: int,
    runner_type: RunnerType,
    research_session: ResearchSession,
    workflow_file: str = "run_full_experiment_with_claude_code_v2.yml",
    github_client: GithubClient = Provide[SyncContainer.github_client],
) -> bool:
    if (
        not research_session.current_iteration
        or not research_session.current_iteration.experiment_runs
    ):
        logger.error("No experiment runs found in current_iteration")
        return False

    executor = WorkflowExecutor(github_client)
    runner_type_setting = runner_info_dict[runner_type]["runner_setting"]

    base_inputs = {
        "experiment_iteration": str(experiment_iteration),
        "runner_type": runner_type_setting,
    }

    tasks = []
    for exp_run in research_session.current_iteration.experiment_runs:
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


@inject
async def execute_evaluation(
    github_repository: GitHubRepositoryInfo,
    experiment_iteration: int,
    research_session: ResearchSession,
    workflow_file: str = "run_evaluation_with_claude_code.yml",
    github_client: GithubClient = Provide[SyncContainer.github_client],
) -> bool:
    if (
        not research_session.current_iteration
        or not research_session.current_iteration.experiment_runs
    ):
        logger.error("No experiment runs found in current_iteration")
        return False

    executor = WorkflowExecutor(github_client)

    branch_name = github_repository.branch_name
    run_ids = [run.run_id for run in research_session.current_iteration.experiment_runs]

    logger.info(f"Executing evaluation on main branch '{branch_name}'")
    logger.info(f"Evaluation will process {len(run_ids)} runs: {', '.join(run_ids)}")

    inputs = {
        "experiment_iteration": str(experiment_iteration),
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
