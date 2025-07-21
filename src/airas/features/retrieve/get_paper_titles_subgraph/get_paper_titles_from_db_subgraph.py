import json
import logging

from langgraph.graph import END, START, StateGraph
from langgraph.graph.graph import CompiledGraph
from typing_extensions import TypedDict

from airas.core.base import BaseSubgraph
from airas.features.retrieve.get_paper_titles_subgraph.input_data import (
    get_paper_titles_subgraph_input_data,
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


class GetPaperTitlesFromDBHiddenState(TypedDict): ...


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

    def __init__(self):
        pass

    @get_paper_titles_from_db_timed
    def _get_paper_titles_from_airas_db(
        self, state: GetPaperTitlesFromDBState
    ) -> dict[str, list[str]]:
        titles = get_paper_titles_from_airas_db(
            queries=state["queries"],  # TODO: フィルタリングロジックを分離する
        )
        return {"titles": titles or []}

    def build_graph(self) -> CompiledGraph:
        graph_builder = StateGraph(GetPaperTitlesFromDBState)
        graph_builder.add_node(
            "get_paper_titles_from_airas_db", self._get_paper_titles_from_airas_db
        )

        graph_builder.add_edge(START, "get_paper_titles_from_airas_db")
        graph_builder.add_edge("get_paper_titles_from_airas_db", END)
        return graph_builder.compile()


def main():
    input = get_paper_titles_subgraph_input_data
    result = GetPaperTitlesFromDBSubgraph().run(input)
    print(f"result: {json.dumps(result, indent=2)}")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        logger.error(f"An error occurred: {e}")
        raise
