import pytest
from airas.publication.html_subgraph.html_subgraph import HtmlSubgraph


@pytest.fixture
def dummy_input():
    return {
        "paper_content": {
            "Title": "Test Paper",
            "Abstract": "This is a test abstract.",
            "Introduction": "Test introduction.",
        }
    }


@pytest.fixture
def expected_output():
    return {
        "paper_html_content": "<div>HTML Content</div>",
        "full_html": "<html><body>HTML Content</body></html>",
    }


def test_html_subgraph(dummy_input, expected_output):
    subgraph = HtmlSubgraph(llm_name="gpt-4o-mini-2024-07-18", save_dir="/tmp")
    graph = subgraph.build_graph()
    result = graph.invoke(dummy_input)
    assert "HTML Content" in result["full_html"]
