import json
import logging
import os
from typing import Any

from langgraph.graph import END, START, StateGraph
from langgraph.graph.graph import CompiledGraph
from typing_extensions import TypedDict

from airas.core.base import BaseSubgraph
from airas.features.retrieve.retrieve_paper_content_subgraph.input_data import (
    retrieve_paper_content_subgraph_input_data,
)

# from airas.types.arxiv import ArxivInfo
# from airas.types.research_study ResearchStudy
from airas.features.retrieve.retrieve_paper_content_subgraph.nodes.retrieve_arxiv_text_from_url import (
    retrieve_arxiv_text_from_url,
)
from airas.features.retrieve.retrieve_paper_content_subgraph.nodes.search_arxiv_by_titles import (
    search_arxiv_by_titles,
)
from airas.utils.execution_timers import ExecutionTimeState, time_node
from airas.utils.logging_utils import setup_logging

setup_logging()
logger = logging.getLogger(__name__)

retrieve_paper_content_str = "retrieve_paper_content_subgraph"
retrieve_paper_content_timed = lambda f: time_node(retrieve_paper_content_str)(f)  # noqa: E731


class RetrievePaperContentInputState(TypedDict):
    titles: list[str]


class RetrievePaperContentHiddenState(TypedDict): ...


class RetrievePaperContentOutputState(TypedDict):
    # arxiv_infos: list[ArxivInfo]
    # research_studies: list[ResearchStudy]
    arxiv_info_list: list[dict[str, Any]]
    research_study_list: list[dict[str, Any]]


class RetrievePaperContentState(
    RetrievePaperContentInputState,
    RetrievePaperContentHiddenState,
    RetrievePaperContentOutputState,
    ExecutionTimeState,
): ...


class RetrievePaperContentSubgraph(BaseSubgraph):
    InputState = RetrievePaperContentInputState
    OutputState = RetrievePaperContentOutputState

    def __init__(self, save_dir: str):
        self.save_dir = save_dir
        self.papers_dir = os.path.join(self.save_dir, "papers")
        os.makedirs(self.papers_dir, exist_ok=True)

    @retrieve_paper_content_timed
    def _search_arxiv(
        self, state: RetrievePaperContentState
    ) -> dict[str, list[dict[str, Any]]]:
        arxiv_info_list = search_arxiv_by_titles(  # TODO: UI上でヒットするが、ここで取得できない例が存在する
            titles=state["titles"],
        )
        return {"arxiv_info_list": arxiv_info_list}

    @retrieve_paper_content_timed
    def _retrieve_arxiv_text_from_url(
        self, state: RetrievePaperContentState
    ) -> dict[str, list[dict[str, Any]]]:
        research_study_list = []

        for arxiv_info in state.get("arxiv_info_list", []):
            full_text = retrieve_arxiv_text_from_url(
                papers_dir=self.papers_dir,
                arxiv_url=arxiv_info.get("arxiv_url", ""),
            )

            research_study = {
                "title": arxiv_info.get("title", ""),
                "full_text": full_text,
            }
            research_study_list.append(research_study)

        return {"research_study_list": research_study_list}

    def build_graph(self) -> CompiledGraph:
        graph_builder = StateGraph(RetrievePaperContentState)
        graph_builder.add_node("search_arxiv", self._search_arxiv)
        graph_builder.add_node(
            "retrieve_arxiv_text_from_url", self._retrieve_arxiv_text_from_url
        )

        graph_builder.add_edge(START, "search_arxiv")
        graph_builder.add_edge("search_arxiv", "retrieve_arxiv_text_from_url")
        graph_builder.add_edge("retrieve_arxiv_text_from_url", END)
        return graph_builder.compile()


def main():
    save_dir = "/workspaces/airas/data"
    input_data = retrieve_paper_content_subgraph_input_data
    result = RetrievePaperContentSubgraph(save_dir=save_dir).run(input_data)
    print(f"result: {json.dumps(result, indent=2)}")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        logger.error(f"An error occurred: {e}")
        raise
