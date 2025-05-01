from unittest.mock import patch, MagicMock
from airas.retrieve.retrieve_paper_subgraph.nodes.arxiv_api_node import ArxivNode


# Normal case test: search_paper returns a list of validated papers
@patch("airas.retrieve.retrieve_paper_subgraph.nodes.arxiv_api_node.requests.get")
@patch("airas.retrieve.retrieve_paper_subgraph.nodes.arxiv_api_node.feedparser.parse")
def test_search_paper_success(mock_feedparser, mock_requests):
    mock_response = MagicMock()
    mock_response.text = "dummy xml"
    mock_response.raise_for_status.return_value = None
    mock_requests.return_value = mock_response
    mock_feedparser.return_value.entries = [
        MagicMock(
            id="http://arxiv.org/abs/1234.5678v1",
            title="Test Paper",
            authors=[
                type("A", (), {"name": "Alice"})()
            ],  # .name属性がstrのダミーオブジェクト
            published="2024-01-01",
            summary="summary",
        )
    ]
    node = ArxivNode()
    result = node.search_paper("test query")
    assert isinstance(result, list)
    assert result[0]["arxiv_id"] == "1234.5678v1"


# Abnormal case test: search_paper returns empty list on API error
@patch(
    "airas.retrieve.retrieve_paper_subgraph.nodes.arxiv_api_node.requests.get",
    side_effect=__import__("requests").exceptions.RequestException("API error"),
)
@patch(
    "airas.retrieve.retrieve_paper_subgraph.nodes.arxiv_api_node.feedparser.parse",
    return_value=MagicMock(entries=[]),
)
def test_search_paper_api_error(mock_feedparser, mock_requests):
    node = ArxivNode(max_retries=1)
    result = node.search_paper("test query")
    assert result == []
