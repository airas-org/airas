from unittest.mock import MagicMock, patch

import pytest
import requests

from airas.preparation.prepare_repository_subgraph.nodes.check_branch_existence import (
    check_branch_existence,
)


# Normal case test: returns sha string when status_code is 200
@patch(
    "airas.preparation.prepare_repository_subgraph.nodes.check_branch_existence.requests.get"
)
def test_check_branch_existence_found(mock_get):
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"commit": {"sha": "abc123"}}
    mock_get.return_value = mock_response
    assert check_branch_existence("owner", "repo", "branch", max_retries=1) == "abc123"


# Normal case test: returns empty string when status_code is 404
@patch(
    "airas.preparation.prepare_repository_subgraph.nodes.check_branch_existence.requests.get"
)
def test_check_branch_existence_not_found(mock_get):
    mock_response = MagicMock()
    mock_response.status_code = 404
    mock_get.return_value = mock_response
    assert check_branch_existence("owner", "repo", "branch", max_retries=1) == ""


# Abnormal case test: raises RuntimeError on 301
@patch(
    "airas.preparation.prepare_repository_subgraph.nodes.check_branch_existence.requests.get"
)
def test_check_branch_existence_moved(mock_get):
    mock_response = MagicMock()
    mock_response.status_code = 301
    mock_get.return_value = mock_response
    with pytest.raises(RuntimeError):
        check_branch_existence("owner", "repo", "branch", max_retries=1)


# Abnormal case test: raises RuntimeError after max retries on request exception
@patch(
    "airas.preparation.prepare_repository_subgraph.nodes.check_branch_existence.requests.get",
    side_effect=requests.RequestException("fail"),
)
def test_check_branch_existence_request_exception(mock_get):
    with pytest.raises(RuntimeError):
        check_branch_existence("owner", "repo", "branch", max_retries=1)
