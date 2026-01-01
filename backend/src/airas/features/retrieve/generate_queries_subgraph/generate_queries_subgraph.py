import logging
from typing import Annotated

from langgraph.graph import END, START, StateGraph
from pydantic import BaseModel, Field
from typing_extensions import TypedDict

from airas.config.llm_config import DEFAULT_NODE_LLMS
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
from airas.services.api_client.langchain_client import LangChainClient
from airas.services.api_client.llm_specs import LLM_MODELS
from airas.utils.execution_timers import ExecutionTimeState, time_node
from airas.utils.logging_utils import setup_logging

setup_logging()
logger = logging.getLogger(__name__)

generate_queries_str = "generate_queries_subgraph"
generate_queries_timed = lambda f: time_node(generate_queries_str)(f)  # noqa: E731


class GenerateQueriesLLMMapping(BaseModel):
    generate_queries: LLM_MODELS = DEFAULT_NODE_LLMS["generate_queries"]


class GenerateQueriesInputState(TypedDict):
    research_topic: str


class GenerateQueriesHiddenState(TypedDict): ...


class GenerateQueriesOutputState(TypedDict):
    queries: list[str]  # TODO: Supporting semantic search


class GenerateQueriesState(
    GenerateQueriesInputState,
    GenerateQueriesHiddenState,
    GenerateQueriesOutputState,
    ExecutionTimeState,
): ...


class GenerateQueriesSubgraph(BaseSubgraph):
    InputState = GenerateQueriesInputState
    OutputState = GenerateQueriesOutputState

    def __init__(
        self,
        llm_client: LangChainClient,
        llm_mapping: dict[str, str] | GenerateQueriesLLMMapping | None = None,
        n_queries: Annotated[int, Field(gt=0)] = 5,
    ):
        if llm_mapping is None:
            self.llm_mapping = GenerateQueriesLLMMapping()
        elif isinstance(llm_mapping, dict):
            self.llm_mapping = GenerateQueriesLLMMapping(**llm_mapping)
        elif isinstance(llm_mapping, GenerateQueriesLLMMapping):
            # すでに型が正しい場合も受け入れる
            self.llm_mapping = llm_mapping
        else:
            raise TypeError(
                f"llm_mapping must be None, dict[str, str], or GenerateQueriesLLMMapping, "
                f"but got {type(llm_mapping)}"
            )
        self.n_queries = n_queries
        self.llm_client = llm_client

    @generate_queries_timed
    async def _generate_queries(
        self, state: GenerateQueriesState
    ) -> dict[str, list[str]]:
        generated_queries = await generate_queries(
            llm_name=self.llm_mapping.generate_queries,
            llm_client=self.llm_client,
            prompt_template=generate_queries_prompt,
            research_topic=state["research_topic"],
            n_queries=self.n_queries,
        )
        return {"queries": generated_queries}

    def build_graph(self):
        graph_builder = StateGraph(GenerateQueriesState)
        graph_builder.add_node("generate_queries", self._generate_queries)
        graph_builder.add_edge(START, "generate_queries")
        graph_builder.add_edge("generate_queries", END)
        return graph_builder.compile()


def main():
    from airas.services.api_client.api_clients_container import sync_container

    sync_container.wire(modules=[__name__])
    input = generate_queries_subgraph_input_data
    result = GenerateQueriesSubgraph().run(input)
    print(f"result: {result}")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        logger.error(f"Error running GenerateQueriesSubgraph: {e}")
        raise
