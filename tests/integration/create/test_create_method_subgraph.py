import pytest
from unittest.mock import patch
from airas.create.create_method_subgraph.create_method_subgraph import (
    CreateMethodSubgraph,
)


@pytest.fixture
def dummy_input():
    return {
        "base_method_text": "Base method",
        "add_method_texts": ["Add method 1", "Add method 2"],
    }


@pytest.fixture
def expected_output():
    return {"new_method": "Generated new method"}


@patch(
    "airas.create_method_subgraph.create_method_subgraph.generator_node",
    return_value="Generated new method",
)
def test_create_method_subgraph(mock_generator_node, dummy_input, expected_output):
    subgraph = CreateMethodSubgraph(llm_name="gpt-4o-mini-2024-07-18")
    graph = subgraph.build_graph()
    result = graph.invoke(dummy_input)
    assert result["new_method"] == expected_output["new_method"]
