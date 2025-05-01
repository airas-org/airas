import pytest
from unittest.mock import patch
from airas.execution.executor_subgraph.nodes.execute_github_actions_workflow import (
    execute_github_actions_workflow,
)


# Normal case: All external dependencies are mocked and a workflow_run_id is returned
@patch(
    "airas.execution.executor_subgraph.nodes.execute_github_actions_workflow._parse_workflow_run_id",
    return_value=12345,
)
@patch(
    "airas.execution.executor_subgraph.nodes.execute_github_actions_workflow._request_github_actions_workflow_info_after_execution",
    return_value={
        "workflow_runs": [
            {"id": 12345, "status": "completed", "created_at": "2024-01-01T00:00:00Z"}
        ]
    },
)
@patch(
    "airas.execution.executor_subgraph.nodes.execute_github_actions_workflow._request_github_actions_workflow_execution"
)
@patch(
    "airas.execution.executor_subgraph.nodes.execute_github_actions_workflow._request_github_actions_workflow_info_before_execution",
    return_value={
        "workflow_runs": [
            {"id": 12344, "status": "completed", "created_at": "2023-12-31T00:00:00Z"}
        ]
    },
)
@patch("os.makedirs")
def test_execute_github_actions_workflow_success(
    mock_makedirs, mock_info_before, mock_execute, mock_info_after, mock_parse_id
):
    result = execute_github_actions_workflow(
        github_owner="owner", repository_name="repo", branch_name="main"
    )
    assert result == 12345


# Abnormal case: _request_github_actions_workflow_info_before_execution returns None
@patch(
    "airas.execution.executor_subgraph.nodes.execute_github_actions_workflow._request_github_actions_workflow_info_before_execution",
    return_value=None,
)
@patch("os.makedirs")
def test_execute_github_actions_workflow_info_before_fail(
    mock_makedirs, mock_info_before
):
    with pytest.raises(RuntimeError):
        execute_github_actions_workflow(
            github_owner="owner", repository_name="repo", branch_name="main"
        )
