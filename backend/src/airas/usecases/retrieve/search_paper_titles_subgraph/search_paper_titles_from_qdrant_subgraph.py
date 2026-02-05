import logging
from typing import Annotated

from langgraph.graph import END, START, StateGraph
from pydantic import BaseModel, Field
from typing_extensions import TypedDict

from airas.core.execution_timers import ExecutionTimeState, time_node
from airas.core.llm_config import DEFAULT_NODE_LLM_CONFIG, NodeLLMConfig
from airas.core.logging_utils import setup_logging
from airas.infra.litellm_client import LiteLLMClient
from airas.infra.qdrant_client import QdrantClient
from airas.usecases.retrieve.search_paper_titles_subgraph.nodes.search_paper_titles_from_qdrant import (
    search_paper_titles_from_qdrant,
)

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


class SearchPaperTitlesFromQdrantLLMMapping(BaseModel):
    search_paper_titles_from_qdrant: NodeLLMConfig = DEFAULT_NODE_LLM_CONFIG[
        "search_paper_titles_from_qdrant"
    ]


class SearchPaperTitlesFromQdrantSubgraph:
    def __init__(
        self,
        litellm_client: LiteLLMClient,
        qdrant_client: QdrantClient,
        collection_name: str,
        papers_per_query: Annotated[int, Field(gt=0)] = 3,
        llm_mapping: SearchPaperTitlesFromQdrantLLMMapping | None = None,
    ):
        self.litellm_client = litellm_client
        self.qdrant_client = qdrant_client
        self.collection_name = collection_name
        self.papers_per_query = papers_per_query
        self.llm_mapping = llm_mapping or SearchPaperTitlesFromQdrantLLMMapping()

    @record_execution_time
    async def _search_paper_titles(
        self, state: SearchPaperTitlesFromQdrantState
    ) -> dict[str, list[str]]:
        results = await search_paper_titles_from_qdrant(
            queries=state["queries"],
            max_results_per_query=self.papers_per_query,
            litellm_client=self.litellm_client,
            qdrant_client=self.qdrant_client,
            collection_name=self.collection_name,
            embedding_model=self.llm_mapping.search_paper_titles_from_qdrant.llm_name,
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
