import json
import logging

from langgraph.graph import END, START, StateGraph
from langgraph.graph.graph import CompiledGraph
from typing_extensions import TypedDict

from airas.core.base import BaseSubgraph
from airas.features.retrieve.generate_queries_subgraph.input_data import (
    generate_queries_subgraph_input_data,
)
from airas.features.retrieve.generate_queries_subgraph.nodes.generate_queries import (
    generate_queries,
)
from airas.features.retrieve.generate_queries_subgraph.prompt.generate_queries_prompt import (
    generate_queries_prompt,
)
from airas.services.api_client.llm_client.llm_facade_client import LLM_MODEL
from airas.utils.check_api_key import check_api_key
from airas.utils.execution_timers import ExecutionTimeState, time_node
from airas.utils.logging_utils import setup_logging

setup_logging()
logger = logging.getLogger(__name__)

generate_queries_str = "generate_queries_subgraph"
generate_queries_timed = lambda f: time_node(generate_queries_str)(f)  # noqa: E731


class GenerateQueriesInputState(TypedDict):
    user_prompt: str


class GenerateQueriesHiddenState(TypedDict): ...


class GenerateQueriesOutputState(TypedDict):
    queries: list[str]  # TODO: 意味検索に対応させる


class GenerateQueriesState(
    GenerateQueriesInputState,
    GenerateQueriesHiddenState,
    GenerateQueriesOutputState,
    ExecutionTimeState,
): ...


class GenerateQueriesSubgraph(BaseSubgraph):
    InputState = GenerateQueriesInputState
    OutputState = GenerateQueriesOutputState

    def __init__(self, llm_name: LLM_MODEL):
        self.llm_name = llm_name
        check_api_key(llm_api_key_check=True)

    @generate_queries_timed
    def _generate_queries(self, state: GenerateQueriesState) -> dict[str, list[str]]:
        generated_queries = generate_queries(
            llm_name=self.llm_name,
            prompt_template=generate_queries_prompt,
            user_prompt=state["user_prompt"],
        )
        return {"queries": generated_queries}

    def build_graph(self) -> CompiledGraph:
        graph_builder = StateGraph(GenerateQueriesState)
        graph_builder.add_node("generate_queries", self._generate_queries)
        graph_builder.add_edge(START, "generate_queries")
        graph_builder.add_edge("generate_queries", END)
        return graph_builder.compile()


def main():
    llm_name = "o3-mini-2025-01-31"
    input = generate_queries_subgraph_input_data
    result = GenerateQueriesSubgraph(
        llm_name=llm_name,
    ).run(input)
    print(f"result: {json.dumps(result, indent=2)}")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        logger.error(f"Error running GenerateQueriesSubgraph: {e}")
        raise
