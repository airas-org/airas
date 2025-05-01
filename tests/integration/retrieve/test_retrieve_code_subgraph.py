import pytest
from unittest.mock import patch
from airas.retrieve.retrieve_code_subgraph.retrieve_code_subgraph import (
    RetrieveCodeSubgraph,
)


@pytest.fixture
def dummy_input():
    return {
        "base_github_url": "https://github.com/test/repo",
        "base_method_text": "Test method",
    }


@pytest.fixture
def expected_output():
    return {"experimental_code": "print('experiment')", "experimental_info": "info"}


@patch(
    "airas.retrieve.retrieve_code_subgraph.node.retrieve_repository_contents._retrieve_file_data",
    return_value="print('experiment')",
)
@patch(
    "airas.retrieve.retrieve_code_subgraph.node.retrieve_repository_contents._retrieve_repository_tree",
    return_value={"tree": [{"path": "test.py", "type": "blob"}]},
)
@patch(
    "airas.retrieve.retrieve_code_subgraph.node.extract_experimental_info.extract_experimental_info",
    return_value=("print('experiment')", "info"),
)
def test_retrieve_code_subgraph(
    mock_extract_info,
    mock_retrieve_tree,
    mock_retrieve_file_data,
    dummy_input,
    expected_output,
):
    subgraph = RetrieveCodeSubgraph()
    graph = subgraph.build_graph()
    result = graph.invoke(dummy_input)
    assert result["experimental_code"] == expected_output["experimental_code"]
    assert result["experimental_info"] == expected_output["experimental_info"]
