import pytest
from unittest.mock import patch, MagicMock
import requests
from airas.preparation.prepare_repository_subgraph.nodes.retrieve_main_branch_sha import (
    retrieve_main_branch_sha,
)


# Normal case test: returns sha string when status_code is 200
@patch(
    "airas.preparation.prepare_repository_subgraph.nodes.retrieve_main_branch_sha.requests.get"
)
def test_retrieve_main_branch_sha_success(mock_get):
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"commit": {"sha": "mainsha123"}}
    mock_get.return_value = mock_response
    assert retrieve_main_branch_sha("owner", "repo", max_retries=1) == "mainsha123"


# Abnormal case test: raises RuntimeError on 301
@patch(
    "airas.preparation.prepare_repository_subgraph.nodes.retrieve_main_branch_sha.requests.get"
)
def test_retrieve_main_branch_sha_moved(mock_get):
    mock_response = MagicMock()
    mock_response.status_code = 301
    mock_get.return_value = mock_response
    with pytest.raises(RuntimeError):
        retrieve_main_branch_sha("owner", "repo", max_retries=1)


# Abnormal case test: raises RuntimeError after max retries on HTTPError
@patch(
    "airas.preparation.prepare_repository_subgraph.nodes.retrieve_main_branch_sha.requests.get",
    side_effect=requests.RequestException("fail"),
)
def test_retrieve_main_branch_sha_request_exception(mock_get):
    with pytest.raises(RuntimeError):
        retrieve_main_branch_sha("owner", "repo", max_retries=1)
