from unittest.mock import patch, MagicMock
from airas.retrieve.retrieve_paper_subgraph.nodes.extract_github_url_node import (
    ExtractGithubUrlNode,
)
import pytest


# Normal case test: returns correct GitHub URL from text and LLM
@patch(
    "airas.retrieve.retrieve_paper_subgraph.nodes.extract_github_url_node.LLMFacadeClient.structured_outputs",
    return_value=({"index": 0}, 0.01),
)
@patch(
    "airas.retrieve.retrieve_paper_subgraph.nodes.extract_github_url_node.requests.get",
    return_value=MagicMock(status_code=200, raise_for_status=lambda: None),
)
def test_extract_github_url_success(mock_requests, mock_structured_outputs):
    node = ExtractGithubUrlNode(llm_name="gpt-4o-mini-2024-07-18")
    text = "Check this repo: https://github.com/user/repo"
    summary = "summary"
    result = node.execute(text, summary)
    assert result == "https://github.com/user/repo"


# Abnormal case test: returns empty string if no valid GitHub URL
@patch(
    "airas.retrieve.retrieve_paper_subgraph.nodes.extract_github_url_node.LLMFacadeClient.structured_outputs",
    return_value=(None, 0.01),
)
@patch(
    "airas.retrieve.retrieve_paper_subgraph.nodes.extract_github_url_node.requests.get",
    return_value=MagicMock(status_code=404, raise_for_status=lambda: None),
)
def test_extract_github_url_no_url(mock_requests, mock_structured_outputs):
    node = ExtractGithubUrlNode(llm_name="gpt-4o-mini-2024-07-18")
    text = "No github url here"
    summary = "summary"
    result = node.execute(text, summary)
    assert result == ""


# Abnormal case test: returns empty string if LLM returns None
@patch(
    "airas.retrieve.retrieve_paper_subgraph.nodes.extract_github_url_node.LLMFacadeClient.structured_outputs",
    return_value=(None, 0.01),
)
@patch(
    "airas.retrieve.retrieve_paper_subgraph.nodes.extract_github_url_node.requests.get",
    return_value=MagicMock(status_code=200, raise_for_status=lambda: None),
)
def test_extract_github_url_vertexai_none(mock_requests, mock_structured_outputs):
    node = ExtractGithubUrlNode(llm_name="gpt-4o-mini-2024-07-18")
    text = "Check this repo: https://github.com/user/repo"
    summary = "summary"
    with pytest.raises(ValueError) as excinfo:
        node.execute(text, summary)
    assert "No response from LLM" in str(excinfo.value)
