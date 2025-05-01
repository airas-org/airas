from unittest.mock import patch
from airas.retrieve.retrieve_paper_subgraph.nodes.extract_paper_title_node import (
    extract_paper_title_node,
)


# Normal case: openai_client returns valid paper_titles for each scraped result
@patch(
    "airas.utils.api_client.llm_facade_client.LLMFacadeClient.structured_outputs",
    side_effect=[
        ({"paper_titles": ["Title1", "Title2"]}, 0.0),
        ({"paper_titles": ["Title3"]}, 0.0),
    ],
)
def test_extract_paper_title_node_success(mock_openai):
    llm_name = "gpt-4o-mini-2024-07-18"
    queries = ["query1"]
    scraped_results = ["result1", "result2"]
    result = extract_paper_title_node(llm_name, queries, scraped_results)
    assert result == ["Title1", "Title2", "Title3"]


# Abnormal case: openai_client returns None for one result
@patch(
    "airas.utils.api_client.llm_facade_client.LLMFacadeClient.structured_outputs",
    side_effect=[(None, None), ({"paper_titles": ["Title3"]}, 0.0)],
)
def test_extract_paper_title_node_partial_none(mock_openai):
    llm_name = "gpt-4o-mini-2024-07-18"
    queries = ["query1"]
    scraped_results = ["result1", "result2"]
    result = extract_paper_title_node(llm_name, queries, scraped_results)
    assert result == ["Title3"]
