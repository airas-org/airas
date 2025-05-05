import pytest

import airas.analysis.analytic_subgraph.nodes.analytic_node as mod
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
    "structured_return, expected",
    [
        ({"analysis_report": "This is a report."}, "This is a report."),
        (None, None),
        ({}, None),
    ],
)
def test_analytic_node(
    monkeypatch: pytest.MonkeyPatch,
    sample_inputs: dict[str, str],
    structured_return: dict[str, str],
    expected: None | str,
    dummy_llm_facade_client,
):
    dummy_llm_facade_client._next_return = structured_return
    monkeypatch.setattr(mod, "LLMFacadeClient", dummy_llm_facade_client)
    result = analytic_node(**sample_inputs)
    assert result == expected
