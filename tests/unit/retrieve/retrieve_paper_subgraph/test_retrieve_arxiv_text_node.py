import pytest
from unittest.mock import patch, mock_open
from airas.retrieve.retrieve_paper_subgraph.nodes.retrieve_arxiv_text_node import (
    RetrievearXivTextNode,
)


# Normal case: text file exists, should read and return its content
@patch("os.path.exists", return_value=True)
@patch("builtins.open", new_callable=mock_open, read_data="test content")
def test_retrieve_arxiv_text_node_text_exists(mock_file, mock_exists):
    node = RetrievearXivTextNode(papers_dir="/dummy")
    result = node.execute("https://arxiv.org/abs/1234.5678v1")
    assert result == "test content"


# Abnormal case: PDF download fails
@patch("os.path.exists", return_value=False)
@patch(
    "airas.retrieve.retrieve_paper_subgraph.nodes.retrieve_arxiv_text_node.requests.get",
    side_effect=Exception("download error"),
)
def test_retrieve_arxiv_text_node_pdf_download_fail(mock_get, mock_exists):
    node = RetrievearXivTextNode(papers_dir="/dummy")
    with pytest.raises(Exception) as excinfo:
        node.execute("https://arxiv.org/abs/1234.5678v1")
    assert "download error" in str(excinfo.value)
