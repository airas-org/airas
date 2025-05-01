import pytest
from unittest.mock import patch
import requests
from airas.preparation.prepare_repository_subgraph.nodes.fork_repository import (
    fork_repository,
)


# Normal case test: returns True when status_code is 202
@patch(
    "airas.preparation.prepare_repository_subgraph.nodes.fork_repository.requests.post"
)
def test_fork_repository_success(mock_post):
    mock_post.return_value.status_code = 202
    assert (
        fork_repository("repo", device_type="cpu", organization="", max_retries=1)
        is True
    )


# Abnormal case test: raises RuntimeError on 400
@patch(
    "airas.preparation.prepare_repository_subgraph.nodes.fork_repository.requests.post"
)
def test_fork_repository_bad_request(mock_post):
    mock_post.return_value.status_code = 400
    with pytest.raises(RuntimeError):
        fork_repository("repo", device_type="cpu", organization="", max_retries=1)


# Abnormal case test: raises RuntimeError on 403
@patch(
    "airas.preparation.prepare_repository_subgraph.nodes.fork_repository.requests.post"
)
def test_fork_repository_forbidden(mock_post):
    mock_post.return_value.status_code = 403
    with pytest.raises(RuntimeError):
        fork_repository("repo", device_type="cpu", organization="", max_retries=1)


# Abnormal case test: raises RuntimeError on 404
@patch(
    "airas.preparation.prepare_repository_subgraph.nodes.fork_repository.requests.post"
)
def test_fork_repository_not_found(mock_post):
    mock_post.return_value.status_code = 404
    with pytest.raises(RuntimeError):
        fork_repository("repo", device_type="cpu", organization="", max_retries=1)


# Abnormal case test: raises RuntimeError on 422
@patch(
    "airas.preparation.prepare_repository_subgraph.nodes.fork_repository.requests.post"
)
def test_fork_repository_validation_failed(mock_post):
    mock_post.return_value.status_code = 422
    with pytest.raises(RuntimeError):
        fork_repository("repo", device_type="cpu", organization="", max_retries=1)


# Abnormal case test: raises RuntimeError after max retries on request exception
@patch(
    "airas.preparation.prepare_repository_subgraph.nodes.fork_repository.requests.post",
    side_effect=requests.RequestException("fail"),
)
def test_fork_repository_request_exception(mock_post):
    with pytest.raises(RuntimeError):
        fork_repository("repo", device_type="cpu", organization="", max_retries=1)
