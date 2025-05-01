import pytest
from typing import Any


class DummyLLMFacadeClient:
    _next_return: Any = None

    def __init__(self, llm_name: str):
        self.llm_name = llm_name

    def structured_outputs(
        self, *, message, data_model
    ) -> tuple[dict[Any, Any] | None, float]:
        if isinstance(self._next_return, dict):
            return self._next_return, 0.0
        return None, 0.0


@pytest.fixture
def dummy_llm_facade_client():
    return DummyLLMFacadeClient
