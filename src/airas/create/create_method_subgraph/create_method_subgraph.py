import logging

from langgraph.graph import START, END, StateGraph
from langgraph.graph.graph import CompiledGraph
from typing import TypedDict

from airas.utils.logging_utils import setup_logging
from airas.create.create_method_subgraph.nodes.generator_node import generator_node

from airas.utils.execution_timers import time_node, ExecutionTimeState
from airas.utils.github_utils.graph_wrapper import create_wrapped_subgraph

setup_logging()
logger = logging.getLogger(__name__)


class CreateMethodSubgraphInputState(TypedDict):
    base_method_text: str
    add_method_texts: list[str]


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
        llm_name: str,
    ):
        self.llm_name = llm_name

    @time_node("create_method_subgraph", "_generator_node")
    def _generator_node(self, state: CreateMethodSubgraphState) -> dict:
        logger.info("---CreateMethodSubgraph---")
        new_method = generator_node(
            llm_name=self.llm_name,
            base_method_text=state["base_method_text"],
            add_method_text_list=state["add_method_texts"],
        )
        return {"new_method": new_method}

    def build_graph(self) -> CompiledGraph:
        graph_builder = StateGraph(CreateMethodSubgraphState)
        # make nodes
        graph_builder.add_node("generator_node", self._generator_node)
        # make edges
        graph_builder.add_edge(START, "generator_node")
        graph_builder.add_edge("generator_node", END)

        return graph_builder.compile()


CreateMethod = create_wrapped_subgraph(
    CreateMethodSubgraph,
    CreateMethodSubgraphInputState,
    CreateMethodSubgraphHiddenState,
)

if __name__ == "__main__":
    # llm_name = "o3-mini-2025-01-31"
    # subgraph = CreateMethodSubgraph(
    #     llm_name=llm_name,
    # ).build_graph()

    # result = subgraph.invoke(create_method_subgraph_input_data)
    # print(result)

    github_repository = "auto-res2/test-tanaka-2"
    branch_name = "test"

    cm = CreateMethod(
        github_repository=github_repository,
        branch_name=branch_name,
        llm_name="o3-mini-2025-01-31",
    )

    result = cm.run()
    print(f"result: {result}")
