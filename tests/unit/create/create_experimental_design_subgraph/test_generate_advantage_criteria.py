import pytest
from unittest.mock import patch
from airas.create.create_experimental_design_subgraph.nodes.generate_advantage_criteria import (
    generate_advantage_criteria,
)


# Normal case test: generate_advantage_criteria returns expected string.
@patch(
    "airas.create.create_experimental_design_subgraph.nodes.generate_advantage_criteria.OpenAIClient.generate",
    return_value=("criteria result", 0.01),
)
def test_generate_advantage_criteria_success(mock_generate):
    result = generate_advantage_criteria(
        llm_name="o3-mini-2025-01-31", new_method="method"
    )
    assert result == "criteria result"


# Abnormal case test: generate_advantage_criteria raises ValueError when OpenAIClient.generate returns (None, ...).
@patch(
    "airas.create.create_experimental_design_subgraph.nodes.generate_advantage_criteria.OpenAIClient.generate",
    return_value=(None, 0.01),
)
def test_generate_advantage_criteria_no_response(mock_generate):
    with pytest.raises(ValueError):
        generate_advantage_criteria(llm_name="o3-mini-2025-01-31", new_method="method")
