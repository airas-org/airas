from unittest.mock import patch

import pytest

from airas.retrieve.retrieve_paper_from_query_subgraph2.retrieve_paper_from_query_subgraph import (
    RetrievePaperFromQuerySubgraph,
)


@pytest.fixture
def dummy_input():
    return {"base_queries": ["test query"]}


@pytest.fixture
def expected_output():
    return {
        "base_github_url": "https://github.com/test/repo",
        "base_method_text": {
            "arxiv_id": "1234",
            "title": "Test Paper",
        },
    }


@patch(
    "airas.retrieve.retrieve_paper_from_query_subgraph.retrieve_paper_from_query_subgraph.web_scrape",
    return_value=["dummy scraped result"],
)
@patch(
    "airas.retrieve.retrieve_paper_from_query_subgraph.retrieve_paper_from_query_subgraph.extract_paper_title",
    return_value=["Test Paper"],
)
@patch(
    "airas.retrieve.retrieve_paper_from_query_subgraph.retrieve_paper_from_query_subgraph.search_arxiv",
    return_value=[
        {
            "arxiv_id": "1234",
            "arxiv_url": "https://arxiv.org/abs/1234",
            "title": "Test Paper",
            "authors": ["A"],
            "published_date": "2025-01-01",
            "summary": "S",
        }
    ],
)
@patch(
    "airas.retrieve.retrieve_paper_from_query_subgraph.retrieve_paper_from_query_subgraph.retrieve_arxiv_text_from_url",
    return_value="full text",
)
@patch(
    "airas.retrieve.retrieve_paper_from_query_subgraph.retrieve_paper_from_query_subgraph.extract_github_url_from_text",
    return_value="https://github.com/test/repo",
)
@patch(
    "airas.retrieve.retrieve_paper_from_query_subgraph.retrieve_paper_from_query_subgraph.summarize_paper",
    return_value=("main", "method", "exp", "lim", "future"),
)
@patch(
    "airas.retrieve.retrieve_paper_from_query_subgraph.retrieve_paper_from_query_subgraph.select_best_paper",
    return_value=["1234"],
)
@patch(
    "airas.retrieve.retrieve_paper_from_query_subgraph.retrieve_paper_from_query_subgraph.check_api_key"
)
@patch(
    "airas.retrieve.retrieve_paper_from_query_subgraph.nodes.web_scrape.FireCrawlClient"
)
def test_retrieve_paper_subgraph(
    mock_firecrawl_client,
    mock_check_api_key,
    mock_select_best,
    mock_summarize,
    mock_extract_github,
    mock_retrieve_text,
    mock_arxiv_execute,
    mock_extract_title,
    mock_web_scrape,
    dummy_input,
    expected_output,
):
    subgraph = RetrievePaperFromQuerySubgraph(
        llm_name="dummy-llm",
        save_dir="/tmp",
        scrape_urls=["https://example.com"],
        arxiv_query_batch_size=1,
        arxiv_num_retrieve_paper=1,
        arxiv_period_days=1,
    )
    graph = subgraph.build_graph()
    result = graph.invoke(dummy_input)
    assert "base_github_url" in result
    assert "base_method_text" in result
