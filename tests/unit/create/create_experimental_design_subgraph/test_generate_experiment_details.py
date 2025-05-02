import pytest
import airas.create.create_experimental_design_subgraph.nodes.generate_experiment_details as mod
from airas.create.create_experimental_design_subgraph.nodes.generate_experiment_details import (
    generate_experiment_details,
)


@pytest.fixture
def sample_inputs():
    return {
        "llm_name": "dummy-llm",
        "verification_policy": "policy",
        "base_experimental_code": "code",
        "base_experimental_info": "info",
    }


@pytest.mark.parametrize(
    "facade_return, expected, mode",
    [
        (("details result", 0.01), "details result", "success"),
        ((None, 0.01), None, "ValueError"),
    ],
)
def test_generate_experiment_details_success_and_failure(
    monkeypatch,
    dummy_llm_facade_client,
    sample_inputs,
    facade_return,
    expected,
    mode,
):
    dummy_llm_facade_client._next_return = facade_return
    monkeypatch.setattr(mod, "LLMFacadeClient", dummy_llm_facade_client)

    match mode:
        case "success":
            result = generate_experiment_details(**sample_inputs)
            assert result == expected
        case "ValueError":
            with pytest.raises(ValueError):
                generate_experiment_details(**sample_inputs)
        case _:
            raise NotImplementedError(f"Unsupported mode: {mode}")
