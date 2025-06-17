import json
import logging
from typing import Any

from langgraph.graph import END, START, StateGraph
from langgraph.graph.graph import CompiledGraph
from typing_extensions import TypedDict

from airas.core.create.create_method_subgraph.input_data import (
    create_method_subgraph_input_data,
)
from airas.core.create.create_method_subgraph.nodes.generator_node import generator_node
from airas.types.paper import CandidatePaperInfo
from airas.services.api_client.llm_client.llm_facade_client import LLM_MODEL
from airas.utils.check_api_key import check_api_key
from airas.utils.execution_timers import ExecutionTimeState, time_node
from airas.utils.logging_utils import setup_logging

setup_logging()
logger = logging.getLogger(__name__)

create_method_timed = lambda f: time_node("create_method_subgraph")(f)  # noqa: E731


class CreateMethodSubgraphInputState(TypedDict):
    base_method_text: CandidatePaperInfo
    add_method_texts: list[CandidatePaperInfo]


class CreateMethodSubgraphHiddenState(TypedDict):
    pass


class CreateMethodSubgraphOutputState(TypedDict):
    new_method: str

class CreateMethodSubgraphState(
    CreateMethodSubgraphInputState,
    CreateMethodSubgraphHiddenState,
    CreateMethodSubgraphOutputState,
    ExecutionTimeState,
):
    pass


class CreateMethodSubgraph:
    def __init__(
        self,
        llm_name: LLM_MODEL,
    ):
        self.llm_name = llm_name
        check_api_key(llm_api_key_check=True)

    @create_method_timed
    def _generator_node(self, state: CreateMethodSubgraphState) -> dict:
        logger.info("---CreateMethodSubgraph---")
        new_method = generator_node(
            llm_name=self.llm_name,
            base_method_text=state["base_method_text"],
            add_method_texts=state["add_method_texts"],
        )
        return {"new_method": new_method}

    def build_graph(self) -> CompiledGraph:
        graph_builder = StateGraph(CreateMethodSubgraphState)
        graph_builder.add_node("generator_node", self._generator_node)
        
        graph_builder.add_edge(START, "generator_node")
        graph_builder.add_edge("generator_node", END)
        return graph_builder.compile()
    
    def run(
        self, 
        state: dict[str, Any], 
        config: dict | None = None
    ) -> dict[str, Any]:
        input_state_keys = CreateMethodSubgraphInputState.__annotations__.keys()
        output_state_keys = CreateMethodSubgraphOutputState.__annotations__.keys()

        input_state = {k: state[k] for k in input_state_keys if k in state}
        result = self.build_graph().invoke(input_state, config=config or {})
        output_state = {k: result[k] for k in output_state_keys if k in result}

        cleaned_state = {k: v for k, v in state.items() if k != "subgraph_name"}

        return {
            "subgraph_name": self.__class__.__name__,
            **cleaned_state,
            **output_state, 
        }


def main():
    llm_name = "o3-mini-2025-01-31"
    input = create_method_subgraph_input_data
    result = CreateMethodSubgraph(
        llm_name=llm_name,
    ).run(input)
    print(f"result: {json.dumps(result, indent=2)}")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        logger.error(f"Error running CreateMethodSubgraph: {e}")
        raise
