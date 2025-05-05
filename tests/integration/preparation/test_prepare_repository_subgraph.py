from unittest.mock import patch

import pytest

from airas.preparation.prepare_repository_subgraph.prepare_repository_subgraph import (
    PrepareRepository,
)


@pytest.fixture
def dummy_input():
    return {"github_repository": "test-owner/test-repo", "branch_name": "test-branch"}


@pytest.fixture
def expected_output():
    return {
        "repository_exists": True,
        "fork_result": True,
        "target_branch_sha": "sha123",
        "main_sha": "sha_main",
        "create_result": True,
        "github_owner": "test-owner",
        "repository_name": "test-repo",
    }


@patch(
    "airas.preparation.prepare_repository_subgraph.prepare_repository_subgraph.fork_repository",
    return_value=True,
)
@patch(
    "airas.preparation.prepare_repository_subgraph.prepare_repository_subgraph.check_github_repository",
    return_value=True,
)
@patch(
    "airas.preparation.prepare_repository_subgraph.prepare_repository_subgraph.check_branch_existence",
    return_value="sha123",
)
@patch(
    "airas.preparation.prepare_repository_subgraph.prepare_repository_subgraph.retrieve_main_branch_sha",
    return_value="sha_main",
)
@patch(
    "airas.preparation.prepare_repository_subgraph.prepare_repository_subgraph.create_branch",
    return_value=True,
)
def test_prepare_repository_subgraph(
    mock_create_branch,
    mock_retrieve_main_sha,
    mock_check_branch_existence,
    mock_check_github_repo,
    mock_fork_repo,
    dummy_input,
    expected_output,
):
    subgraph = PrepareRepository(device_type="cpu", organization="test-org")
    graph = subgraph.build_graph()
    result = graph.invoke(dummy_input)
    print("DEBUG result:", result)
    assert result["repository_exists"] == expected_output["repository_exists"]
    assert result["fork_result"] == expected_output["fork_result"]
    assert result["target_branch_sha"] == expected_output["target_branch_sha"]
    assert result["main_sha"] == expected_output["main_sha"]
    assert result["create_result"] == expected_output["create_result"]
    assert result["github_owner"] == expected_output["github_owner"]
    assert result["repository_name"] == expected_output["repository_name"]
