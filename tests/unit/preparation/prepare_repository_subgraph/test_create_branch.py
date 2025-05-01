import pytest
from unittest.mock import patch, MagicMock
import requests
from airas.preparation.prepare_repository_subgraph.nodes.create_branch import (
    create_branch,
)


# Normal case test: returns True when status_code is 201
@patch(
    "airas.preparation.prepare_repository_subgraph.nodes.create_branch.requests.post"
)
def test_create_branch_success(mock_post):
    mock_response = MagicMock()
    mock_response.status_code = 201
    mock_post.return_value = mock_response
    assert create_branch("owner", "repo", "branch", "sha", max_retries=1) is True


# Abnormal case test: raises RuntimeError on 409
@patch(
    "airas.preparation.prepare_repository_subgraph.nodes.create_branch.requests.post"
)
def test_create_branch_conflict(mock_post):
    mock_response = MagicMock()
    mock_response.status_code = 409
    mock_post.return_value = mock_response
    with pytest.raises(RuntimeError):
        create_branch("owner", "repo", "branch", "sha", max_retries=1)


# Abnormal case test: raises RuntimeError on 422
@patch(
    "airas.preparation.prepare_repository_subgraph.nodes.create_branch.requests.post"
)
def test_create_branch_validation_failed(mock_post):
    mock_response = MagicMock()
    mock_response.status_code = 422
    mock_response.json.return_value = {"message": "validation error"}
    mock_post.return_value = mock_response
    with pytest.raises(RuntimeError):
        create_branch("owner", "repo", "branch", "sha", max_retries=1)


# Abnormal case test: raises RuntimeError after max retries on HTTPError
@patch(
    "airas.preparation.prepare_repository_subgraph.nodes.create_branch.requests.post",
    side_effect=requests.RequestException("fail"),
)
def test_create_branch_request_exception(mock_post):
    with pytest.raises(RuntimeError):
        create_branch("owner", "repo", "branch", "sha", max_retries=1)
