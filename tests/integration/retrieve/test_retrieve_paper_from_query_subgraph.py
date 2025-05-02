import pytest
from unittest.mock import patch
from airas.retrieve.retrieve_paper_subgraph.retrieve_paper_subgraph import (
    RetrievePaperSubgraph,
)


@pytest.fixture
def dummy_input():
    return {"queries": ["test query"]}


@pytest.fixture
def expected_output():
    return {
        "base_github_url": "https://github.com/test/repo",
        "base_method_text": '{"title": "Test Paper"}',
        "add_github_urls": ["https://github.com/test/repo2"],
        "add_method_texts": ['{"title": "Add Paper"}'],
    }


@patch(
    "airas.retrieve.retrieve_paper_subgraph.nodes.web_scrape_node.web_scrape_node",
    return_value=["dummy scraped result"],
)
@patch(
    "airas.retrieve.retrieve_paper_subgraph.nodes.extract_paper_title_node.extract_paper_title_node",
    return_value=["Test Paper"],
)
@patch(
    "airas.retrieve.retrieve_paper_subgraph.nodes.arxiv_api_node.ArxivNode.execute",
    return_value=[
        {
            "arxiv_id": "1234",
            "arxiv_url": "https://arxiv.org/abs/1234",
            "title": "Test Paper",
            "authors": ["A"],
            "published_date": "2025-01-01",
            "journal": "J",
            "doi": "D",
            "summary": "S",
        }
    ],
)
@patch(
    "airas.retrieve.retrieve_paper_subgraph.nodes.retrieve_arxiv_text_node.RetrievearXivTextNode.execute",
    return_value="full text",
)
@patch(
    "airas.retrieve.retrieve_paper_subgraph.nodes.extract_github_url_node.ExtractGithubUrlNode.execute",
    return_value="https://github.com/test/repo",
)
@patch(
    "airas.retrieve.retrieve_paper_subgraph.nodes.summarize_paper_node.summarize_paper_node",
    return_value=("main", "method", "exp", "lim", "future"),
)
@patch(
    "airas.retrieve.retrieve_paper_subgraph.nodes.select_best_paper_node.select_best_paper_node",
    return_value=["1234"],
)
@patch(
    "airas.retrieve.retrieve_paper_subgraph.nodes.generate_queries_node.generate_queries_node",
    return_value=["add query"],
)
def test_retrieve_paper_subgraph(
    mock_generate_queries,
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
    subgraph = RetrievePaperSubgraph(
        llm_name="dummy-llm",
        save_dir="/tmp",
        scrape_urls=["https://example.com"],
        arxiv_query_batch_size=1,
        arxiv_num_retrieve_paper=1,
        arxiv_period_days=1,
        add_paper_num=1,
    )
    graph = subgraph.build_graph()
    result = graph.invoke(dummy_input)
    assert "base_github_url" in result
    assert "base_method_text" in result
    assert "add_github_urls" in result
    assert "add_method_texts" in result
