from unittest.mock import patch

from airas.retrieve.retrieve_paper_subgraph.nodes.web_scrape_node import web_scrape_node


# Normal case: firecrawl_scrape returns valid markdown for each query/url
@patch(
    "airas.retrieve.retrieve_paper_subgraph.nodes.web_scrape_node.FIRE_CRAWL_API_KEY",
    "dummy-key",
)
@patch(
    "airas.retrieve.retrieve_paper_subgraph.nodes.web_scrape_node.firecrawl_scrape",
    return_value={"data": {"markdown": "scraped content"}},
)
def test_web_scrape_node_success(mock_scrape):
    queries = ["query1"]
    scrape_urls = ["https://example.com"]
    result = web_scrape_node(queries, scrape_urls)
    assert result == ["scraped content"]


# Abnormal case: FIRE_CRAWL_API_KEY is not set
@patch(
    "airas.retrieve.retrieve_paper_subgraph.nodes.web_scrape_node.FIRE_CRAWL_API_KEY",
    None,
)
def test_web_scrape_node_no_api_key():
    queries = ["query1"]
    scrape_urls = ["https://example.com"]
    result = web_scrape_node(queries, scrape_urls)
    assert result == []
