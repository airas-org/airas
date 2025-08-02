import time
from logging import getLogger

from airas.services.api_client.github_client import GithubClient
from airas.types.latex import LATEX_TEMPLATE

logger = getLogger(__name__)

_POLL_INTERVAL_SEC = 10
_TIMEOUT_SEC = 600


def execute_latex_compile(
    github_owner: str,
    repository_name: str,
    branch_name: str,
    latex_template: LATEX_TEMPLATE = "iclr2024",
) -> bool:
    LATEX_COMPILED_WORKFLOW_FILE = "compile_latex.yml"
    client = GithubClient()
    workflow_runs_data = client.list_workflow_runs(
        github_owner, repository_name, branch_name
    )
    if workflow_runs_data is None:
        raise ValueError(
            f"Failed to get baseline workflow count for {github_owner}/{repository_name} on branch {branch_name}"
        )
    base_workflow_run_count = workflow_runs_data["total_count"]
    success = client.create_workflow_dispatch(
        github_owner,
        repository_name,
        LATEX_COMPILED_WORKFLOW_FILE,
        ref=branch_name,
        inputs={"subdir": latex_template},
    )
    if not success:
        raise ValueError(
            f"Failed to dispatch workflow {LATEX_COMPILED_WORKFLOW_FILE} for {github_owner}/{repository_name} on branch {branch_name}"
        )

    start_time = time.time()
    while True:
        time.sleep(_POLL_INTERVAL_SEC)
        response = client.list_workflow_runs(github_owner, repository_name, branch_name)
        if not response:
            raise ValueError(
                f"Failed to retrieve workflow runs for {github_owner}/{repository_name} on branch {branch_name}"
            )
        current_workflow_run_count = response["total_count"]
        if (
            current_workflow_run_count >= base_workflow_run_count
            and response["workflow_runs"][0]["status"] == "completed"
        ):
            return True
        if time.time() - start_time > _TIMEOUT_SEC:
            raise TimeoutError(
                f"Workflow execution timed out after {_TIMEOUT_SEC} seconds"
            )
        continue


if __name__ == "__main__":
    github_owner = "auto-res2"
    repository_name = "tanaka-20250803-v3"
    branch_name = "main"
    result = execute_latex_compile(
        github_owner=github_owner,
        repository_name=repository_name,
        branch_name=branch_name,
        latex_template="iclr2024",
    )
