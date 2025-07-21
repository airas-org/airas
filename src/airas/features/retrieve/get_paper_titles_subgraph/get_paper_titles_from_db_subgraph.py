import json
import logging
from typing import Any

from langgraph.graph import END, START, StateGraph
from langgraph.graph.graph import CompiledGraph
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
from airas.utils.execution_timers import ExecutionTimeState, time_node
from airas.utils.logging_utils import setup_logging

setup_logging()
logger = logging.getLogger(__name__)

get_paper_titles_from_db_str = "get_paper_titles_from_db_subgraph"
get_paper_titles_from_db_timed = lambda f: time_node(get_paper_titles_from_db_str)(f)  # noqa: E731


class GetPaperTitlesFromDBInputState(TypedDict):
    queries: list[str]


class GetPaperTitlesFromDBHiddenState(TypedDict):
    all_papers: list[dict[str, Any]]


class GetPaperTitlesFromDBOutputState(TypedDict):
    titles: list[str]


class GetPaperTitlesFromDBState(
    GetPaperTitlesFromDBInputState,
    GetPaperTitlesFromDBHiddenState,
    GetPaperTitlesFromDBOutputState,
    ExecutionTimeState,
): ...


class GetPaperTitlesFromDBSubgraph(BaseSubgraph):
    InputState = GetPaperTitlesFromDBInputState
    OutputState = GetPaperTitlesFromDBOutputState

    def __init__(
        self,
        num_retrieve_paper: int = 5,
        semantic_search: bool = False,
    ):
        self.num_retrieve_paper = num_retrieve_paper
        self.semantic_search = semantic_search

    @get_paper_titles_from_db_timed
    def _get_paper_titles_from_airas_db(self, state: GetPaperTitlesFromDBState) -> dict:
        all_papers = get_paper_titles_from_airas_db()
        return {"all_papers": all_papers or []}

    @get_paper_titles_from_db_timed
    def _filter_titles_by_queries(
        self, state: GetPaperTitlesFromDBState
    ) -> dict[str, list[str]]:
        titles = filter_titles_by_queries(
            papers=state["all_papers"],
            queries=state["queries"],
            num_retrieve_paper=self.num_retrieve_paper,
        )
        return {"titles": titles or []}

    @get_paper_titles_from_db_timed
    def get_paper_titles_from_qdrant(self, state: GetPaperTitlesFromDBState) -> dict:
        titles = get_paper_titles_from_qdrant(
            num_retrieve_paper=self.num_retrieve_paper, queries=state["queries"]
        )
        return {"titles": titles or []}

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
        num_retrieve_paper=5, semantic_search=True
    ).run(input)
    print(f"result: {json.dumps(result, indent=2)}")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        logger.error(f"An error occurred: {e}")
        raise
