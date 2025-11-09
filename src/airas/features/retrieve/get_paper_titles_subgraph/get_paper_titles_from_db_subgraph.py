import logging
from typing import Any

from dependency_injector import providers
from dependency_injector.wiring import Provide, inject
from langgraph.graph import END, START, StateGraph
from langgraph.graph.graph import CompiledGraph
from pydantic import BaseModel
from typing_extensions import TypedDict

from airas.core.base import BaseSubgraph
from airas.features.retrieve.get_paper_titles_subgraph.input_data import (
    get_paper_titles_subgraph_input_data,
)
from airas.features.retrieve.get_paper_titles_subgraph.nodes.filter_titles_by_queries import (
    filter_titles_by_queries,
)
from airas.features.retrieve.get_paper_titles_subgraph.nodes.get_paper_title_from_qdrant import (
    get_paper_titles_from_qdrant,
)
from airas.features.retrieve.get_paper_titles_subgraph.nodes.get_paper_titles_from_airas_db import (
    get_paper_titles_from_airas_db,
)
from airas.services.api_client.api_clients_container import SyncContainer
from airas.services.api_client.llm_client.llm_facade_client import (
    LLM_MODEL,
    LLMFacadeClient,
)
from airas.services.api_client.qdrant_client import QdrantClient
from airas.types.research_study import ResearchStudy
from airas.utils.check_api_key import check_api_key
from airas.utils.execution_timers import ExecutionTimeState, time_node
from airas.utils.logging_utils import setup_logging

setup_logging()
logger = logging.getLogger(__name__)

get_paper_titles_from_db_str = "get_paper_titles_from_db_subgraph"
get_paper_titles_from_db_timed = lambda f: time_node(get_paper_titles_from_db_str)(f)  # noqa: E731


class GetPaperTitlesFromDBLLMMapping(BaseModel):
    embedding_model: LLM_MODEL = "gemini-embedding-001"


class GetPaperTitlesFromDBInputState(TypedDict):
    queries: list[str]


class GetPaperTitlesFromDBHiddenState(TypedDict):
    all_papers: list[dict[str, Any]]


class GetPaperTitlesFromDBOutputState(TypedDict):
    research_study_list: list[ResearchStudy]


class GetPaperTitlesFromDBState(
    GetPaperTitlesFromDBInputState,
    GetPaperTitlesFromDBHiddenState,
    GetPaperTitlesFromDBOutputState,
    ExecutionTimeState,
): ...


class GetPaperTitlesFromDBSubgraph(BaseSubgraph):
    InputState = GetPaperTitlesFromDBInputState
    OutputState = GetPaperTitlesFromDBOutputState

    @inject
    def __init__(
        self,
        max_results_per_query: int = 3,
        semantic_search: bool = False,
        qdrant_client: QdrantClient = Provide[SyncContainer.qdrant_client],
        llm_facade_provider: providers.Factory[LLMFacadeClient] = Provide[
            SyncContainer.llm_facade_provider
        ],
    ):
        self.qdrant_client = qdrant_client
        self.llm_facade_provider = llm_facade_provider
        self.max_results_per_query = max_results_per_query
        self.semantic_search = semantic_search
        self.llm_mapping = GetPaperTitlesFromDBLLMMapping()
        if semantic_search:
            check_api_key(qdrant_api_key_check=True)

    @get_paper_titles_from_db_timed
    def _get_paper_titles_from_airas_db(
        self, state: GetPaperTitlesFromDBState
    ) -> dict[str, list[dict[str, Any]]]:
        all_papers = get_paper_titles_from_airas_db()
        return {"all_papers": all_papers or []}

    @get_paper_titles_from_db_timed
    def _filter_titles_by_queries(
        self, state: GetPaperTitlesFromDBState
    ) -> dict[str, list[ResearchStudy]]:
        titles = filter_titles_by_queries(
            papers=state["all_papers"],
            queries=state["queries"],
            max_results_per_query=self.max_results_per_query,
        )
        research_study_list = [ResearchStudy(title=title) for title in (titles or [])]
        return {"research_study_list": research_study_list}

    @get_paper_titles_from_db_timed
    def get_paper_titles_from_qdrant(
        self, state: GetPaperTitlesFromDBState
    ) -> dict[str, list[ResearchStudy]]:
        titles = get_paper_titles_from_qdrant(
            num_retrieve_paper=self.max_results_per_query,
            queries=state["queries"],
            qdrant_client=self.qdrant_client,
            llm_client=self.llm_facade_provider(
                llm_name=self.llm_mapping.embedding_model
            ),
        )
        research_study_list = [ResearchStudy(title=title) for title in (titles or [])]
        return {"research_study_list": research_study_list}

    def select_database(self, state: GetPaperTitlesFromDBState) -> str:
        if self.semantic_search:
            return "qdrant"
        return "airas_db"

    def build_graph(self) -> CompiledGraph:
        graph_builder = StateGraph(GetPaperTitlesFromDBState)
        graph_builder.add_node(
            "get_paper_titles_from_airas_db", self._get_paper_titles_from_airas_db
        )
        graph_builder.add_node(
            "filter_titles_by_queries", self._filter_titles_by_queries
        )
        graph_builder.add_node(
            "get_paper_titles_from_qdrant", self.get_paper_titles_from_qdrant
        )

        graph_builder.add_conditional_edges(
            START,
            self.select_database,
            {
                "airas_db": "get_paper_titles_from_airas_db",
                "qdrant": "get_paper_titles_from_qdrant",
            },
        )
        graph_builder.add_edge(
            "get_paper_titles_from_airas_db", "filter_titles_by_queries"
        )
        graph_builder.add_edge("filter_titles_by_queries", END)
        graph_builder.add_edge("get_paper_titles_from_qdrant", END)
        return graph_builder.compile()


def main():
    input = get_paper_titles_subgraph_input_data
    result = GetPaperTitlesFromDBSubgraph(
        max_results_per_query=3, semantic_search=True
    ).run(input)
    print(f"result: {result}")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        logger.error(f"An error occurred: {e}")
        raise
