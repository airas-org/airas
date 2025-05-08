import pytest

from airas.analysis.analytic_subgraph.nodes.analytic_node import analytic_node


@pytest.fixture
def sample_inputs() -> dict[str, str]:
    return {
        "llm_name": "dummy-llm",
        "new_method": "new method",
        "verification_policy": "policy",
        "experiment_code": "code",
        "output_text_data": "output",
    }


@pytest.mark.parametrize(
    "dummy_return, expected",
    [
        ({"analysis_report": "This is a report."}, "This is a report."),
        (None, None),
        ({}, None),
    ],
)
def test_analytic_node(
    sample_inputs: dict[str, str],
    dummy_return: dict[str, str],
    expected: None | str,
    dummy_llm_facade_client,
):
    client = dummy_llm_facade_client(sample_inputs["llm_name"])
    client._next_return = dummy_return

    result = analytic_node(**sample_inputs, client=client)
    assert result == expected
