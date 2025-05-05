from unittest.mock import patch

import pytest

from airas.analysis.analytic_subgraph.analytic_subgraph import AnalyticSubgraph


@pytest.fixture
def dummy_input():
    return {
        "new_method": "Test Method",
        "verification_policy": "Test Policy",
        "experiment_code": "print('test')",
        "output_text_data": "Test output",
    }


@pytest.fixture
def expected_output():
    return {"analysis_report": "Test analysis report"}


@patch(
    "airas.analysis.analytic_subgraph.nodes.analytic_node.openai_client",
    return_value='{"analysis_report": "Test analysis report"}',
)
def test_analytic_subgraph(mock_openai_client, dummy_input, expected_output):
    subgraph = AnalyticSubgraph(llm_name="dummy-llm")
    graph = subgraph.build_graph()
    result = graph.invoke(dummy_input)
    assert result["analysis_report"] == "Test analysis report"
