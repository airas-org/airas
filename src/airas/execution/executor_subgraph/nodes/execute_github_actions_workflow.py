import time
from datetime import datetime, timezone
from logging import getLogger

from airas.utils.api_client.github_client import GithubClient

logger = getLogger(__name__)


_WORKFLOW_FILE = "run_experiment.yml"
_POLL_INTERVAL_SEC = 10
_TIMEOUT_SEC = 600


def _count_github_actions_workflow_runs(response: dict) -> int:
    return len(response["workflow_runs"])

def _parse_workflow_run_id(response: dict) -> int:
    latest_id = 0
    latest_timestamp = datetime.min.replace(tzinfo=timezone.utc)
    for res in response["workflow_runs"]:
        created_at = datetime.fromisoformat(res["created_at"].replace("Z", "+00:00"))
        if created_at > latest_timestamp:
            latest_timestamp = created_at
            latest_id = res["id"]
    return latest_id

def _check_confirmation_of_execution_completion(response: dict) -> bool:
    return all(res["status"] == "completed" for res in response["workflow_runs"])

def execute_github_actions_workflow(
    github_owner: str, 
    repository_name: str, 
    branch_name: str, 
    *, 
    client: GithubClient | None = None, 
) -> int:
    client = client or GithubClient()

    response_before_execution = client.list_workflow_runs(
        github_owner, repository_name, branch_name
    )
    
    num_workflow_runs_before_execution = _count_github_actions_workflow_runs(response_before_execution)
    logger.info(f"Number of workflow runs before execution:{num_workflow_runs_before_execution}")

    ok_dispatch = client.dispatch_workflow(
        github_owner,
        repository_name,
        _WORKFLOW_FILE, 
        ref=branch_name, 
    )
    if not ok_dispatch:
        raise RuntimeError("Failed to dispatch workflow")
    logger.info("Workflow dispatch sent.")

    start = time.time()
    while True:
        response_after_execution = client.list_workflow_runs(
            github_owner, repository_name, branch_name
        )
        if (
            _count_github_actions_workflow_runs(response_after_execution) == num_workflow_runs_before_execution + 1 
            and _check_confirmation_of_execution_completion(response_after_execution)
        ):
            run_id = _parse_workflow_run_id(response_after_execution)
            logger.info(f"Workflow {run_id} completed")
            return run_id
        
        if time.time() - start > _TIMEOUT_SEC:
            raise TimeoutError("Workflow did not finish within timeout.")
        
        time.sleep(_POLL_INTERVAL_SEC)


if __name__ == "__main__":

    github_owner = "auto-res2"
    repository_name = "experiment_script_matsuzawa"
    branch_name = "base-branch-retrievepaperfromquerysubgraph-20250507-121037"
    result = execute_github_actions_workflow(github_owner, repository_name, branch_name)
    print(f"result: {result}")