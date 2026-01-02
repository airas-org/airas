import logging
from typing import Annotated

from langgraph.graph import END, START, StateGraph
from pydantic import BaseModel, Field
from typing_extensions import TypedDict

from airas.core.execution_timers import ExecutionTimeState, time_node
from airas.core.llm_config import DEFAULT_NODE_LLMS
from airas.core.logging_utils import setup_logging
from airas.infra.langchain_client import LangChainClient
from airas.infra.llm_specs import LLM_MODELS
from airas.usecases.generators.generate_queries_subgraph.nodes.generate_queries import (
    generate_queries,
)
from airas.usecases.generators.generate_queries_subgraph.prompt.generate_queries_prompt import (
    generate_queries_prompt,
)

setup_logging()
logger = logging.getLogger(__name__)

record_execution_time = lambda f: time_node("generate_queries_subgraph")(f)  # noqa: E731


class GenerateQueriesLLMMapping(BaseModel):
    generate_queries: LLM_MODELS = DEFAULT_NODE_LLMS["generate_queries"]


class GenerateQueriesInputState(TypedDict):
    research_topic: str


class GenerateQueriesOutputState(TypedDict):
    queries: list[str]


class GenerateQueriesState(
    GenerateQueriesInputState,
    GenerateQueriesOutputState,
    ExecutionTimeState,
): ...


class GenerateQueriesSubgraph:
    def __init__(
        self,
        llm_client: LangChainClient,
        num_paper_search_queries: Annotated[int, Field(gt=0)] = 2,
        llm_mapping: GenerateQueriesLLMMapping | None = None,
    ):
        self.num_paper_search_queries = num_paper_search_queries
        self.llm_client = llm_client
        self.llm_mapping = llm_mapping or GenerateQueriesLLMMapping()

    @record_execution_time
    async def _generate_queries(
        self, state: GenerateQueriesState
    ) -> dict[str, list[str]]:
        generated_queries = await generate_queries(
            llm_name=self.llm_mapping.generate_queries,
            llm_client=self.llm_client,
            prompt_template=generate_queries_prompt,
            research_topic=state["research_topic"],
            num_paper_search_queries=self.num_paper_search_queries,
        )
        return {"queries": generated_queries}

    def build_graph(self):
        graph_builder = StateGraph(GenerateQueriesState)
        graph_builder.add_node("generate_queries", self._generate_queries)
        graph_builder.add_edge(START, "generate_queries")
        graph_builder.add_edge("generate_queries", END)
        return graph_builder.compile()
