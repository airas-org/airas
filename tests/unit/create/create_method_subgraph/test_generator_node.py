import pytest
from unittest.mock import patch
from airas.create.create_method_subgraph.nodes.generator_node import generator_node


# Normal case: returns the expected string when generate returns a valid string
@patch(
    "airas.create.create_method_subgraph.nodes.generator_node.OpenAIClient.generate",
    return_value=("output result", 0.1),
)
def test_generator_node_success(mock_generate):
    result = generator_node(
        llm_name="dummy-model",
        base_method_text="base method",
        add_method_text_list=["add1", "add2"],
    )
    assert result == "output result"


# Abnormal case: raises ValueError when generate returns None
@patch(
    "airas.create.create_method_subgraph.nodes.generator_node.OpenAIClient.generate",
    return_value=(None, 0.1),
)
def test_generator_node_no_response(mock_generate):
    with pytest.raises(ValueError):
        generator_node(
            llm_name="dummy-model",
            base_method_text="base method",
            add_method_text_list=["add1", "add2"],
        )
