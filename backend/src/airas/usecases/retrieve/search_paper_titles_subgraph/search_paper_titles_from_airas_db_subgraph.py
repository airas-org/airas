import logging
from typing import Annotated

from langgraph.graph import END, START, StateGraph
from pydantic import Field
from typing_extensions import TypedDict

from airas.core.execution_timers import ExecutionTimeState, time_node
from airas.core.logging_utils import setup_logging
from airas.usecases.retrieve.search_paper_titles_subgraph.nodes.search_paper_titles_from_airas_db import (
    AirasDbPaperSearchIndex,
    search_paper_titles_from_airas_db,
)

setup_logging()
logger = logging.getLogger(__name__)

subgraph_name = "search_paper_titles_from_airas_db_subgraph"
record_execution_time = lambda f: time_node(subgraph_name)(f)  # noqa: E731


class SearchPaperTitlesFromAirasDbInputState(TypedDict):
    queries: list[str]


class SearchPaperTitlesFromAirasDbOutputState(ExecutionTimeState):
    paper_titles: list[str]


class SearchPaperTitlesFromAirasDbState(
    SearchPaperTitlesFromAirasDbInputState,
    SearchPaperTitlesFromAirasDbOutputState,
): ...


class SearchPaperTitlesFromAirasDbSubgraph:
    def __init__(
        self,
        search_index: AirasDbPaperSearchIndex,
        papers_per_query: Annotated[int, Field(gt=0)] = 3,
    ):
        self.search_index = search_index
        self.papers_per_query = papers_per_query

    @record_execution_time
    async def _search_paper_titles(
        self, state: SearchPaperTitlesFromAirasDbState
    ) -> dict[str, list[str]]:
        results = await search_paper_titles_from_airas_db(
            queries=state["queries"],
            max_results_per_query=self.papers_per_query,
            search_index=self.search_index,
        )

        return {"paper_titles": results}

    def build_graph(self):
        graph_builder = StateGraph(
            SearchPaperTitlesFromAirasDbState,
            input_schema=SearchPaperTitlesFromAirasDbInputState,
            output_schema=SearchPaperTitlesFromAirasDbOutputState,
        )
        graph_builder.add_node("search_paper_titles", self._search_paper_titles)
        graph_builder.add_edge(START, "search_paper_titles")
        graph_builder.add_edge("search_paper_titles", END)
        return graph_builder.compile()
