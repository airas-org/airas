import pytest

import airas.create.create_method_subgraph.nodes.generator_node as mod
from airas.create.create_method_subgraph.nodes.generator_node import generator_node


@pytest.fixture
def sample_inputs():
    return {
        "llm_name": "dummy-model",
        "base_method_text": "base method",
        "add_method_text_list": ["add1", "add2"],
    }


@pytest.mark.parametrize(
    "facade_return, expected, mode",
    [
        (("output result", 0.1), "output result", "success"),
        ((None, 0.1), None, "ValueError"),
    ],
)
def test_generator_node_success_and_failure(
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
            result = generator_node(**sample_inputs)
            assert result == expected
        case "ValueError":
            with pytest.raises(ValueError):
                generator_node(**sample_inputs)
        case _:
            raise NotImplementedError(f"Unsupported mode: {mode}")
