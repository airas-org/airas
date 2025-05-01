import pytest
from unittest.mock import patch
from airas.execution.executor_subgraph.executor_subgraph import ExecutorSubgraph


@pytest.fixture
def dummy_input():
    return {
        "new_method": "Test Method",
        "experiment_code": "print('test')",
        "github_owner": "test-owner",
        "repository_name": "test-repo",
        "branch_name": "test-branch",
    }


@pytest.fixture
def expected_output():
    return {
        "experiment_devin_url": "https://devin.ai/mock",
        "branch_name": "mock_branch",
        "output_text_data": "Mock output",
        "fix_iteration_count": 0,
        "session_id": "mock_session",
        "workflow_run_id": 123456,
        "error_text_data": "Mock error",
        "judgment_result": False,
    }


@patch(
    "airas.execution.executor_subgraph.nodes.generate_code_with_devin.generate_code_with_devin",
    return_value=("mock_session", "https://devin.ai/mock"),
)
@patch(
    "airas.execution.executor_subgraph.nodes.execute_github_actions_workflow.execute_github_actions_workflow",
    return_value=123456,
)
@patch(
    "airas.execution.executor_subgraph.nodes.retrieve_github_actions_artifacts.retrieve_github_actions_artifacts",
    return_value=("Mock output", "Mock error"),
)
@patch(
    "airas.execution.executor_subgraph.nodes.llm_decide.llm_decide", return_value=False
)
@patch(
    "airas.execution.executor_subgraph.nodes.fix_code_with_devin.fix_code_with_devin",
    return_value=0,
)
@patch(
    "airas.execution.executor_subgraph.nodes.check_devin_completion.check_devin_completion",
    return_value=True,
)
def test_executor_subgraph(
    mock_check_devin_completion,
    mock_fix_code_with_devin,
    mock_llm_decide,
    mock_retrieve_artifacts,
    mock_execute_workflow,
    mock_generate_code,
    dummy_input,
    expected_output,
):
    subgraph = ExecutorSubgraph(save_dir="/tmp", max_code_fix_iteration=3)
    graph = subgraph.build_graph()
    # ExecutorSubgraphState expects more keys, so we fill them with dummy values
    state = {
        **dummy_input,
        "experiment_session_id": "mock_session",
        "devin_completion": True,
        "fix_iteration_count": 0,
        "error_text_data": "Mock error",
        "judgment_result": False,
        "workflow_run_id": 123456,
        "experiment_devin_url": "https://devin.ai/mock",
        "branch_name": "mock_branch",
        "output_text_data": "Mock output",
    }
    result = graph.invoke(state)
    assert result["experiment_devin_url"] == expected_output["experiment_devin_url"]
    assert result["branch_name"] == expected_output["branch_name"]
    assert result["output_text_data"] == expected_output["output_text_data"]
