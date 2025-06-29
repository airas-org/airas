# your_package/core/base.py
from abc import ABC, abstractmethod
from typing import Any, TypedDict

from langgraph.graph.graph import CompiledGraph


class BaseSubgraph(ABC):
    InputState: type[TypedDict]
    OutputState: type[TypedDict]

    @abstractmethod
    def build_graph(self) -> CompiledGraph: ...

    def run(self, state: dict[str, Any], config: dict | None = None) -> dict[str, Any]:
        input_state_keys = self.InputState.__annotations__.keys()
        output_state_keys = self.OutputState.__annotations__.keys()

        input_state = {k: state[k] for k in input_state_keys if k in state}
        config = {"recursion_limit": 200}
        result = self.build_graph().invoke(input_state, config=config)
        output_state = {k: result[k] for k in output_state_keys if k in result}

        cleaned_state = {k: v for k, v in state.items() if k != "subgraph_name"}
        return {
            "subgraph_name": self.__class__.__name__,
            **cleaned_state,
            **output_state,
        }
