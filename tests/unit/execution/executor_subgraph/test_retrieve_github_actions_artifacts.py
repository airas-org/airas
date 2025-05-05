from unittest.mock import MagicMock, patch

import pytest

from airas.execution.executor_subgraph.nodes.retrieve_github_actions_artifacts import (
    retrieve_github_actions_artifacts,
)


# Normal case: All external dependencies are mocked, and the contents of output.txt/error.txt are returned
@patch(
    "airas.execution.executor_subgraph.nodes.retrieve_github_actions_artifacts._copy_images_to_latest_dir"
)
@patch(
    "airas.execution.executor_subgraph.nodes.retrieve_github_actions_artifacts.open",
    create=True,
)
@patch(
    "airas.execution.executor_subgraph.nodes.retrieve_github_actions_artifacts._request_download_artifacts"
)
@patch(
    "airas.execution.executor_subgraph.nodes.retrieve_github_actions_artifacts._parse_artifacts_info",
    return_value={"artifact1": "url"},
)
@patch(
    "airas.execution.executor_subgraph.nodes.retrieve_github_actions_artifacts._request_github_actions_artifacts",
    return_value={
        "artifacts": [
            {
                "workflow_run": {"id": "runid"},
                "name": "artifact1",
                "archive_download_url": "url",
            }
        ]
    },
)
@patch("os.makedirs")
def test_retrieve_github_actions_artifacts_success(
    mock_makedirs,
    mock_request_artifacts,
    mock_parse_info,
    mock_download,
    mock_open,
    mock_copy_images,
):
    # The mock for open is set to be used as a context manager and called twice
    mock_file = MagicMock()
    mock_file.read.side_effect = ["output content", "error content"]
    mock_open.side_effect = [
        MagicMock(
            __enter__=lambda s: mock_file,
            __exit__=lambda s, exc_type, exc_val, exc_tb: None,
        ),
        MagicMock(
            __enter__=lambda s: mock_file,
            __exit__=lambda s, exc_type, exc_val, exc_tb: None,
        ),
    ]
    result = retrieve_github_actions_artifacts(
        github_owner="owner",
        repository_name="repo",
        workflow_run_id="runid",
        save_dir="/tmp",
        fix_iteration_count=0,
    )
    assert result == ("output content", "error content")


# Abnormal case: _request_github_actions_artifacts returns None
@patch(
    "airas.execution.executor_subgraph.nodes.retrieve_github_actions_artifacts._copy_images_to_latest_dir"
)
@patch(
    "airas.execution.executor_subgraph.nodes.retrieve_github_actions_artifacts.open",
    create=True,
)
@patch(
    "airas.execution.executor_subgraph.nodes.retrieve_github_actions_artifacts._request_download_artifacts"
)
@patch(
    "airas.execution.executor_subgraph.nodes.retrieve_github_actions_artifacts._parse_artifacts_info",
    return_value={},
)
@patch(
    "airas.execution.executor_subgraph.nodes.retrieve_github_actions_artifacts._request_github_actions_artifacts",
    return_value=None,
)
@patch("os.makedirs")
def test_retrieve_github_actions_artifacts_api_fail(
    mock_makedirs,
    mock_request_artifacts,
    mock_parse_info,
    mock_download,
    mock_open,
    mock_copy_images,
):
    with pytest.raises(Exception):
        retrieve_github_actions_artifacts(
            github_owner="owner",
            repository_name="repo",
            workflow_run_id="runid",
            save_dir="/tmp",
            fix_iteration_count=0,
        )
