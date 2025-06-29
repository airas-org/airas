import time
from dataclasses import dataclass
from logging import getLogger
from typing import Optional

from airas.services.api_client.github_client import GithubClient

logger = getLogger(__name__)

_POLL_INTERVAL_SEC = 10
_TIMEOUT_SEC = 600


@dataclass
class WorkflowResult:
    """Result of a workflow execution"""

    run_id: Optional[int]
    success: bool
    error_message: Optional[str] = None


class WorkflowExecutor:
    """Handles GitHub Actions workflow execution and monitoring"""

    def __init__(self, client: Optional[GithubClient] = None):
        self.client = client or GithubClient()

    def execute_workflow(
        self,
        github_owner: str,
        repository_name: str,
        branch_name: str,
        experiment_iteration: int,
        gpu_enabled: bool = False,
    ) -> WorkflowResult:
        """Execute a GitHub Actions workflow and wait for completion.

        Args:
            github_owner: The owner/organization name of the GitHub repository
            repository_name: The name of the GitHub repository
            branch_name: The branch name to run the workflow on
            gpu_enabled: Whether to use GPU-enabled workflow

        Returns:
            WorkflowResult containing execution status and run ID
        """
        try:
            # Step 1: Get baseline workflow count
            baseline_count = self._get_baseline_workflow_count(
                github_owner, repository_name, branch_name
            )
            if baseline_count is None:
                return WorkflowResult(
                    None, False, "Failed to get baseline workflow count"
                )

            # Step 2: Dispatch workflow
            workflow_file = self._get_workflow_file(gpu_enabled)
            success = self._dispatch_workflow(
                github_owner,
                repository_name,
                workflow_file,
                experiment_iteration,
                branch_name,
            )
            if not success:
                return WorkflowResult(None, False, "Failed to dispatch workflow")

            # Step 3: Wait for completion
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

    def _get_workflow_file(self, gpu_enabled: bool) -> str:
        """Get the appropriate workflow file name"""
        return (
            "run_experiment_on_gpu.yml" if gpu_enabled else "run_experiment_on_cpu.yml"
        )

    def _get_baseline_workflow_count(
        self, github_owner: str, repository_name: str, branch_name: str
    ) -> Optional[int]:
        """Get the current number of workflow runs as baseline"""
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
        workflow_file: str,
        experiment_iteration: int,
        branch_name: str,
    ) -> bool:
        """Dispatch the workflow to GitHub Actions"""
        inputs = {
            "experiment_iteration": str(experiment_iteration),
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
        """Wait for workflow completion and return the run ID"""
        start_time = time.time()

        while True:
            # Check timeout
            if time.time() - start_time > _TIMEOUT_SEC:
                logger.error("Workflow execution timed out")
                return None

            # Get current workflow status
            response = self._get_workflow_runs(
                github_owner, repository_name, branch_name
            )
            if not response:
                time.sleep(_POLL_INTERVAL_SEC)
                continue

            # Check if new workflow completed
            run_id = self._check_for_new_completed_workflow(response, baseline_count)
            if run_id:
                logger.info(f"Workflow {run_id} completed successfully")
                return run_id

            time.sleep(_POLL_INTERVAL_SEC)

    def _get_workflow_runs(
        self, github_owner: str, repository_name: str, branch_name: str
    ) -> Optional[dict]:
        """Safely get workflow runs from GitHub API"""
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
        """Check if a new workflow has completed and return its run ID"""
        workflow_runs = response.get("workflow_runs", [])
        current_count = len(workflow_runs)

        logger.debug(
            f"Current workflow count: {current_count}, baseline: {baseline_count}"
        )

        # Check if new workflow exists and is completed
        if current_count > baseline_count and workflow_runs:
            latest_run = workflow_runs[0]  # Most recent run
            if self._is_workflow_completed(latest_run):
                return latest_run.get("id")

        return None

    def _is_workflow_completed(self, workflow_run: dict) -> bool:
        """Check if a workflow run is completed"""
        status = workflow_run.get("status")
        conclusion = workflow_run.get("conclusion")

        logger.debug(f"Workflow status: {status}, conclusion: {conclusion}")

        # Workflow is completed when status is "completed" and has a conclusion
        return status == "completed" and conclusion is not None


# Legacy function wrapper for backward compatibility
def execute_github_actions_workflow(
    github_repository: str,
    branch_name: str,
    experiment_iteration: int,
    gpu_enabled: bool = False,
    client: Optional[GithubClient] = None,
) -> bool:
    """Execute a GitHub Actions workflow and wait for completion.

    This function dispatches a workflow on GitHub Actions and monitors its execution
    until completion. It supports both CPU and GPU-enabled workflows based on the
    gpu_enabled parameter.

    Args:
        github_repository: The GitHub repository in the format "owner/repo"
        branch_name: The branch name to run the workflow on
        gpu_enabled: Whether to use GPU-enabled workflow. Defaults to False
        client: GitHub API client instance. If None, a new one will be created

    Returns:
        True if execution completed successfully, False otherwise

    Example:
        >>> result = execute_github_actions_workflow(
        ...     github_owner="example-org",
        ...     repository_name="my-repo",
        ...     branch_name="main",
        ...     gpu_enabled=True
        ... )
        >>> print(f"Workflow execution successful: {result}")
    """
    github_owner, repository_name = github_repository.split("/", 1)
    executor = WorkflowExecutor(client)
    result = executor.execute_workflow(
        github_owner, repository_name, branch_name, experiment_iteration, gpu_enabled
    )
    return result.success


if __name__ == "__main__":
    github_repository = "fuyu-quant/airas-temp"
    branch_name = "main"
    result = execute_github_actions_workflow(
        github_repository,
        branch_name,
        experiment_iteration=1,
    )
    print(f"result: {result}")
