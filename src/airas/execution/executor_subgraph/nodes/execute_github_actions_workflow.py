import os
from datetime import datetime, timezone
from airas.utils.api_request_handler import fetch_api_data, retry_request
from logging import getLogger

logger = getLogger(__name__)


def _request_github_actions_workflow_execution(
    headers: dict, github_owner: str, repository_name: str, branch_name: str
):
    workflow_file_name = "run_experiment.yml"
    url = f"https://api.github.com/repos/{github_owner}/{repository_name}/actions/workflows/{workflow_file_name}/dispatches"
    data = {
        "ref": f"{branch_name}",
    }
    return retry_request(fetch_api_data, url, headers=headers, data=data, method="POST")


def _request_github_actions_workflow_info_before_execution(
    headers: dict, github_owner: str, repository_name: str, branch_name: str
):
    url = f"https://api.github.com/repos/{github_owner}/{repository_name}/actions/runs"
    params = {
        "branch": f"{branch_name}",
        "event": "workflow_dispatch",
    }
    return retry_request(
        fetch_api_data, url, headers=headers, params=params, method="GET"
    )


def _request_github_actions_workflow_info_after_execution(
    headers: dict,
    github_owner: str,
    repository_name: str,
    branch_name: str,
    num_workflow_runs_before_execution: int,
):
    url = f"https://api.github.com/repos/{github_owner}/{repository_name}/actions/runs"
    params = {
        "branch": f"{branch_name}",
        "event": "workflow_dispatch",
    }

    # NOTE:The number of runs is increased by one to confirm that execution is complete.
    def should_retry(response) -> bool:
        # Describe the process so that it is True if you want to retry
        num_workflow_runs_after_execution = _count_github_actions_workflow_runs(
            response
        )
        return not (
            (
                num_workflow_runs_after_execution
                == num_workflow_runs_before_execution + 1
            )
            and _check_confirmation_of_execution_completion(response)
        )

    return retry_request(
        fetch_api_data,
        url,
        headers=headers,
        params=params,
        method="GET",
        check_condition=should_retry,
    )


def _count_github_actions_workflow_runs(response: dict) -> int:
    num_workflow_runs = len(response["workflow_runs"])
    return num_workflow_runs


def _parse_workflow_run_id(response: dict):
    workflow_timestamp_dict = {}
    latest_timestamp = datetime.min.replace(tzinfo=timezone.utc)
    for res in response["workflow_runs"]:
        created_at = datetime.fromisoformat(res["created_at"].replace("Z", "+00:00"))
        workflow_timestamp_dict[created_at] = res["id"]
        if created_at > latest_timestamp:
            latest_timestamp = created_at
    return workflow_timestamp_dict[latest_timestamp]


def _check_confirmation_of_execution_completion(response: dict):
    status_list = []
    for res in response["workflow_runs"]:
        status_list.append(res["status"])
    return all(item == "completed" for item in status_list)


def execute_github_actions_workflow(
    github_owner: str, repository_name: str, branch_name: str
) -> int:
    headers = {
        "Accept": "application/vnd.github+json",
        "Authorization": f"Bearer {os.getenv('GITHUB_PERSONAL_ACCESS_TOKEN')}",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    # Check the number of runs before executing workflow
    response_before_execution = _request_github_actions_workflow_info_before_execution(
        headers=headers,
        github_owner=github_owner,
        repository_name=repository_name,
        branch_name=branch_name,
    )
    if response_before_execution:
        logger.info(
            "Successfully retrieved information on Github actions prior to execution of workflow."
        )
    else:
        logger.error(
            f"Failed to fetch workflow info before execution. "
            f"Owner: {github_owner}, Repo: {repository_name}, Branch: {branch_name}"
        )
        raise RuntimeError("Failed to fetch workflow info before execution.")
    num_workflow_runs_before_execution = _count_github_actions_workflow_runs(
        response_before_execution
    )
    logger.info(
        f"Number of workflow runs before execution:{num_workflow_runs_before_execution}"
    )

    # Execute the workflow
    _request_github_actions_workflow_execution(
        headers=headers,
        github_owner=github_owner,
        repository_name=repository_name,
        branch_name=branch_name,
    )

    # Check the number of runs after executing workflow
    response_after_execution = _request_github_actions_workflow_info_after_execution(
        headers,
        github_owner,
        repository_name,
        branch_name,
        num_workflow_runs_before_execution,
    )
    if response_after_execution:
        logger.info(
            "Successfully retrieved information on Github actions after execution of workflow."
        )
    else:
        logger.error(
            f"Failed to fetch workflow info after execution. "
            f"Owner: {github_owner}, Repo: {repository_name}, Branch: {branch_name}"
        )
        raise RuntimeError("Failed to fetch workflow info after execution.")

    workflow_run_id = _parse_workflow_run_id(response_after_execution)

    return workflow_run_id


# if __name__ == "__main__":
#     graph_builder = StateGraph(State)
#     graph_builder.add_node(
#         "retrieve_github_actions_artifacts",
#         ExecuteGithubActionsWorkflowNode(
#             input_key=["github_owner", "repository_name", "branch_name"],
#             output_key=["workflow_run_id"],
#         ),
#     )
#     graph_builder.add_edge(START, "retrieve_github_actions_artifacts")
#     graph_builder.add_edge("retrieve_github_actions_artifacts", END)
#     graph = graph_builder.compile()
#     state = {
#         "github_owner": "auto-res",
#         "repository_name": "experimental-script",
#         "branch_name": "devin/1738251222-learnable-gated-pooling",
#     }
#     graph.invoke(state, debug=True)
