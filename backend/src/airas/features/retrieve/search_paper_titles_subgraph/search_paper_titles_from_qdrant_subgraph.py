import logging
from typing import Annotated

from langgraph.graph import END, START, StateGraph
from pydantic import Field
from typing_extensions import TypedDict

from airas.features.retrieve.search_paper_titles_subgraph.nodes.search_paper_titles_from_qdrant import (
    search_paper_titles_from_qdrant,
)
from airas.services.api_client.llm_client.llm_facade_client import LLMFacadeClient
from airas.services.api_client.qdrant_client import QdrantClient
from airas.utils.execution_timers import ExecutionTimeState, time_node
from airas.utils.logging_utils import setup_logging

setup_logging()
logger = logging.getLogger(__name__)

subgraph_name = "search_paper_titles_from_qdrant_subgraph"
record_execution_time = lambda f: time_node(subgraph_name)(f)  # noqa: E731


class SearchPaperTitlesFromQdrantInputState(TypedDict):
    queries: list[str]


class SearchPaperTitlesFromQdrantOutputState(ExecutionTimeState):
    paper_titles: list[str]


class SearchPaperTitlesFromQdrantState(
    SearchPaperTitlesFromQdrantInputState,
    SearchPaperTitlesFromQdrantOutputState,
): ...


class SearchPaperTitlesFromQdrantSubgraph:
    def __init__(
        self,
        llm_client: LLMFacadeClient,
        qdrant_client: QdrantClient,
        max_results_per_query: Annotated[int, Field(gt=0)] = 3,
    ):
        self.llm_client = llm_client
        self.qdrant_client = qdrant_client
        self.max_results_per_query = max_results_per_query

    @record_execution_time
    async def _search_paper_titles(
        self, state: SearchPaperTitlesFromQdrantState
    ) -> dict[str, list[str]]:
        results = await search_paper_titles_from_qdrant(
            queries=state["queries"],
            max_results_per_query=self.max_results_per_query,
            qdrant_client=self.qdrant_client,
            llm_client=self.llm_client,
        )

        return {"paper_titles": results}

    def build_graph(self):
        graph_builder = StateGraph(
            SearchPaperTitlesFromQdrantState,
            input_schema=SearchPaperTitlesFromQdrantInputState,
            output_schema=SearchPaperTitlesFromQdrantOutputState,
        )
        graph_builder.add_node("search_paper_titles", self._search_paper_titles)
        graph_builder.add_edge(START, "search_paper_titles")
        graph_builder.add_edge("search_paper_titles", END)
        return graph_builder.compile()
