from unittest.mock import patch

import pytest
import requests

from airas.preparation.prepare_repository_subgraph.nodes.check_github_repository import (
    check_github_repository,
)


# Normal case test: returns True when status_code is 200
@patch(
    "airas.preparation.prepare_repository_subgraph.nodes.check_github_repository.requests.get"
)
def test_check_github_repository_exists(mock_get):
    mock_get.return_value.status_code = 200
    assert check_github_repository("owner", "repo") is True


# Normal case test: returns False when status_code is 404
@patch(
    "airas.preparation.prepare_repository_subgraph.nodes.check_github_repository.requests.get"
)
def test_check_github_repository_not_found(mock_get):
    mock_get.return_value.status_code = 404
    assert check_github_repository("owner", "repo") is False


# Abnormal case test: raises RuntimeError on 403
@patch(
    "airas.preparation.prepare_repository_subgraph.nodes.check_github_repository.requests.get"
)
def test_check_github_repository_forbidden(mock_get):
    mock_get.return_value.status_code = 403
    with pytest.raises(RuntimeError):
        check_github_repository("owner", "repo", max_retries=1)


# Abnormal case test: raises RuntimeError on 301
@patch(
    "airas.preparation.prepare_repository_subgraph.nodes.check_github_repository.requests.get"
)
def test_check_github_repository_moved(mock_get):
    mock_get.return_value.status_code = 301
    with pytest.raises(RuntimeError):
        check_github_repository("owner", "repo", max_retries=1)


# Abnormal case test: raises RuntimeError after max retries on request exception
@patch(
    "airas.preparation.prepare_repository_subgraph.nodes.check_github_repository.requests.get",
    side_effect=requests.RequestException("fail"),
)
def test_check_github_repository_request_exception(mock_get):
    with pytest.raises(RuntimeError):
        check_github_repository("owner", "repo", max_retries=1)
