import pytest
from unittest.mock import patch
from airas.create.create_experimental_design_subgraph.nodes.generate_experiment_code import (
    generate_experiment_code,
)


# Normal case test: generate_experiment_code returns expected string.
@patch(
    "airas.create.create_experimental_design_subgraph.nodes.generate_experiment_code.OpenAIClient.generate",
    return_value=("code result", 0.01),
)
def test_generate_experiment_code_success(mock_generate):
    result = generate_experiment_code(
        llm_name="o3-mini-2025-01-31",
        experiment_details="details",
        base_experimental_code="code",
        base_experimental_info="info",
    )
    assert result == "code result"


# Abnormal case test: generate_experiment_code raises ValueError when OpenAIClient.generate returns (None, ...).
@patch(
    "airas.create.create_experimental_design_subgraph.nodes.generate_experiment_code.OpenAIClient.generate",
    return_value=(None, 0.01),
)
def test_generate_experiment_code_no_response(mock_generate):
    with pytest.raises(ValueError):
        generate_experiment_code(
            llm_name="o3-mini-2025-01-31",
            experiment_details="details",
            base_experimental_code="code",
            base_experimental_info="info",
        )
