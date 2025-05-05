import pytest

import airas.create.create_experimental_design_subgraph.nodes.generate_advantage_criteria as mod
from airas.create.create_experimental_design_subgraph.nodes.generate_advantage_criteria import (
    generate_advantage_criteria,
)


@pytest.fixture
def sample_inputs() -> dict[str, str]:
    return {
        "llm_name": "dummy-llm",
        "new_method": "new method",
    }


@pytest.mark.parametrize(
    "facade_return, expected, mode",
    [
        (("criteria result", 0.01), "criteria result", "success"),
        ((None, 0.01), None, "ValueError"),
    ],
)
def test_generate_advantage_criteria(
    monkeypatch: pytest.MonkeyPatch,
    dummy_llm_facade_client,
    sample_inputs: dict[str, str],
    facade_return,
    expected,
    mode,
):
    dummy_llm_facade_client._next_return = facade_return
    monkeypatch.setattr(mod, "LLMFacadeClient", dummy_llm_facade_client)

    match mode:
        case "success":
            result = generate_advantage_criteria(**sample_inputs)
            assert result == expected
        case "ValueError":
            with pytest.raises(ValueError):
                generate_advantage_criteria(**sample_inputs)
        case _:
            raise NotImplementedError(f"Unsupported mode: {mode}")
