import pytest
from unittest.mock import patch
from airas.create.create_experimental_design_subgraph.nodes.generate_experiment_details import (
    generate_experiment_details,
)


# Normal case test: generate_experiment_details returns expected string.
@patch(
    "airas.create.create_experimental_design_subgraph.nodes.generate_experiment_details.OpenAIClient.generate",
    return_value=("details result", 0.01),
)
def test_generate_experiment_details_success(mock_generate):
    result = generate_experiment_details(
        llm_name="o3-mini-2025-01-31",
        verification_policy="policy",
        base_experimental_code="code",
        base_experimental_info="info",
    )
    assert result == "details result"


# Abnormal case test: generate_experiment_details raises ValueError when OpenAIClient.generate returns (None, ...).
@patch(
    "airas.create.create_experimental_design_subgraph.nodes.generate_experiment_details.OpenAIClient.generate",
    return_value=(None, 0.01),
)
def test_generate_experiment_details_no_response(mock_generate):
    with pytest.raises(ValueError):
        generate_experiment_details(
            llm_name="o3-mini-2025-01-31",
            verification_policy="policy",
            base_experimental_code="code",
            base_experimental_info="info",
        )
