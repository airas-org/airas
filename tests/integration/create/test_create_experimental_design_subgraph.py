import pytest
from unittest.mock import patch

from airas.create.create_experimental_design_subgraph.create_experimental_design_subgraph import (
    CreateExperimentalDesignSubgraph,
)


@pytest.fixture
def dummy_input():
    return {
        "new_method": "New Cool Algorithm",
        "base_method_text": "Existing baseline approach",
        "base_experimental_code": "print('baseline experiment')",
        "base_experimental_info": "Info about the baseline experiment",
    }


@pytest.fixture
def expected_output():
    return {
        "verification_policy": "Verification policy generated",
        "experiment_details": "Experiment details generated",
        "experiment_code": "Experiment code generated",
    }


@patch(
    "airas.create.create_experimental_design_subgraph.create_experimental_design_subgraph.generate_experiment_code"
)
@patch(
    "airas.create.create_experimental_design_subgraph.create_experimental_design_subgraph.generate_experiment_details"
)
@patch(
    "airas.create.create_experimental_design_subgraph.create_experimental_design_subgraph.generate_advantage_criteria"
)
def test_create_experimental_design_subgraph(
    mock_criteria, mock_details, mock_code, dummy_input, expected_output
):
    mock_criteria.return_value = expected_output["verification_policy"]
    mock_details.return_value = expected_output["experiment_details"]
    mock_code.return_value = expected_output["experiment_code"]

    subgraph = CreateExperimentalDesignSubgraph()
    graph = subgraph.build_graph()
    result = graph.invoke(dummy_input)

    assert result["verification_policy"] == expected_output["verification_policy"]
    assert result["experiment_details"] == expected_output["experiment_details"]
    assert result["experiment_code"] == expected_output["experiment_code"]
