import time
from dataclasses import dataclass
from logging import getLogger
from typing import Optional

from airas.services.api_client.github_client import GithubClient
from airas.types.github import GitHubRepositoryInfo

logger = getLogger(__name__)

_POLL_INTERVAL_SEC = 10
_TIMEOUT_SEC = 12000  # NOTE: 200 minutes (slightly longer than GitHub Actions timeout of 180 minutes)


@dataclass
class WorkflowResult:
    run_id: Optional[int]
    success: bool
    error_message: Optional[str] = None


class WorkflowExecutor:
    def __init__(self, client: Optional[GithubClient] = None):
        self.client = client or GithubClient()

    def execute_workflow(
        self,
        github_owner: str,
        repository_name: str,
        branch_name: str,
        experiment_iteration: int,
        runner_type: str,
        workflow_file: str,
    ) -> WorkflowResult:
        try:
            baseline_count = self._get_baseline_workflow_count(
                github_owner, repository_name, branch_name
            )
            if baseline_count is None:
                return WorkflowResult(
                    None, False, "Failed to get baseline workflow count"
                )

            success = self._dispatch_workflow(
                github_owner,
                repository_name,
                experiment_iteration,
                branch_name,
                runner_type,
                workflow_file,
            )
            if not success:
                return WorkflowResult(None, False, "Failed to dispatch workflow")

            run_id = self._wait_for_completion(
                github_owner, repository_name, branch_name, baseline_count
            )
            if run_id is None:
                return WorkflowResult(
                    None, False, "Workflow execution timed out or failed"
                )

            return WorkflowResult(run_id, True)

        except Exception as e:
            logger.error(f"Workflow execution failed: {e}")
            return WorkflowResult(None, False, str(e))

    def _get_baseline_workflow_count(
        self, github_owner: str, repository_name: str, branch_name: str
    ) -> Optional[int]:
        try:
            response = self.client.list_workflow_runs(
                github_owner, repository_name, branch_name
            )
            if not response:
                return None
            count = len(response.get("workflow_runs", []))
            logger.info(f"Baseline workflow count: {count}")
            return count
        except Exception as e:
            logger.error(f"Failed to get baseline workflow count: {e}")
            return None

    def _dispatch_workflow(
        self,
        github_owner: str,
        repository_name: str,
        experiment_iteration: int,
        branch_name: str,
        runner_type: str,
        workflow_file: str,
    ) -> bool:
        inputs = {
            "experiment_iteration": str(experiment_iteration),
            "runner_type": runner_type,
        }
        try:
            success = self.client.create_workflow_dispatch(
                github_owner,
                repository_name,
                workflow_file,
                ref=branch_name,
                inputs=inputs,
            )
            if success:
                logger.info("Workflow dispatch sent successfully")
                print(
                    f"Check running workflows: https://github.com/{github_owner}/{repository_name}/actions"
                )
                return True
            else:
                logger.error("Workflow dispatch failed")
                return False
        except Exception as e:
            logger.error(f"Failed to dispatch workflow: {e}")
            return False

    def _wait_for_completion(
        self,
        github_owner: str,
        repository_name: str,
        branch_name: str,
        baseline_count: int,
    ) -> Optional[int]:
        start_time = time.time()

        while True:
            if time.time() - start_time > _TIMEOUT_SEC:
                logger.error("Workflow execution timed out")
                return None

            response = self._get_workflow_runs(
                github_owner, repository_name, branch_name
            )
            if not response:
                time.sleep(_POLL_INTERVAL_SEC)
                continue

            run_id = self._check_for_new_completed_workflow(response, baseline_count)
            if run_id:
                logger.info(f"Workflow {run_id} completed successfully")
                return run_id

            time.sleep(_POLL_INTERVAL_SEC)

    def _get_workflow_runs(
        self, github_owner: str, repository_name: str, branch_name: str
    ) -> Optional[dict]:
        try:
            response = self.client.list_workflow_runs(
                github_owner, repository_name, branch_name
            )
            return response if response else None
        except Exception as e:
            logger.warning(f"Error getting workflow runs: {e}")
            return None

    def _check_for_new_completed_workflow(
        self, response: dict, baseline_count: int
    ) -> Optional[int]:
        workflow_runs = response.get("workflow_runs", [])
        current_count = len(workflow_runs)

        logger.debug(
            f"Current workflow count: {current_count}, baseline: {baseline_count}"
        )

        if current_count > baseline_count and workflow_runs:
            latest_run = workflow_runs[0]  # Most recent run
            if self._is_workflow_completed(latest_run):
                return latest_run.get("id")

        return None

    def _is_workflow_completed(self, workflow_run: dict) -> bool:
        status = workflow_run.get("status")
        conclusion = workflow_run.get("conclusion")

        logger.debug(f"Workflow status: {status}, conclusion: {conclusion}")

        return status == "completed" and conclusion is not None


def execute_github_actions_workflow(
    github_repository: GitHubRepositoryInfo,
    experiment_iteration: int,
    runner_type: str = "ubuntu-latest",
    workflow_file: str = "run_experiment.yml",
    client: Optional[GithubClient] = None,
) -> bool:
    executor = WorkflowExecutor(client)
    result = executor.execute_workflow(
        github_repository.github_owner,
        github_repository.repository_name,
        github_repository.branch_name,
        experiment_iteration,
        runner_type,
        workflow_file,
    )
    return result.success
