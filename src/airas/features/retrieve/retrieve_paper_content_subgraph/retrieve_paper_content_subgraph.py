import json
import logging
import os

from langgraph.graph import END, START, StateGraph
from langgraph.graph.graph import CompiledGraph
from typing_extensions import TypedDict

from airas.core.base import BaseSubgraph
from airas.features.retrieve.retrieve_paper_content_subgraph.input_data import (
    retrieve_paper_content_subgraph_input_data,
)
from airas.features.retrieve.retrieve_paper_content_subgraph.nodes.retrieve_text_from_url import (
    retrieve_text_from_url,
)
from airas.features.retrieve.retrieve_paper_content_subgraph.nodes.search_arxiv_by_title import (
    search_arxiv_by_title,
)
from airas.features.retrieve.retrieve_paper_content_subgraph.nodes.search_openalex_by_title import (
    search_openalex_by_title,
)
from airas.features.retrieve.retrieve_paper_content_subgraph.nodes.search_ss_by_title import (
    search_ss_by_title,
)
from airas.utils.execution_timers import ExecutionTimeState, time_node
from airas.utils.logging_utils import setup_logging

setup_logging()
logger = logging.getLogger(__name__)

retrieve_paper_content_str = "retrieve_paper_content_subgraph"
retrieve_paper_content_timed = lambda f: time_node(retrieve_paper_content_str)(f)  # noqa: E731


class RetrievePaperContentInputState(TypedDict):
    research_study_list: list[dict]


class RetrievePaperContentHiddenState(TypedDict): ...


class RetrievePaperContentOutputState(TypedDict):
    research_study_list: list[dict]


class RetrievePaperContentState(
    RetrievePaperContentInputState,
    RetrievePaperContentHiddenState,
    RetrievePaperContentOutputState,
    ExecutionTimeState,
): ...


class RetrievePaperContentSubgraph(BaseSubgraph):
    InputState = RetrievePaperContentInputState
    OutputState = RetrievePaperContentOutputState

    def __init__(self, save_dir: str, paper_provider: str = "arxiv"):
        self.save_dir = save_dir
        self.papers_dir = os.path.join(self.save_dir, "papers")
        self.paper_provider = paper_provider
        os.makedirs(self.papers_dir, exist_ok=True)

    @retrieve_paper_content_timed
    def _search_arxiv(self, state: RetrievePaperContentState) -> dict[str, list[dict]]:
        research_study_list = state["research_study_list"]

        for research_study in research_study_list:
            title = research_study.get("title", "")
            if title:
                paper_data = search_arxiv_by_title(title=title)
                if paper_data:
                    for key, value in paper_data.items():
                        if key not in research_study or not research_study[key]:
                            research_study[key] = value

        return {"research_study_list": research_study_list}

    @retrieve_paper_content_timed
    def _search_openalex(
        self, state: RetrievePaperContentState
    ) -> dict[str, list[dict]]:
        research_study_list = state["research_study_list"]

        for research_study in research_study_list:
            title = research_study.get("title", "")
            if title:
                paper_data = search_openalex_by_title(title=title)
                if paper_data:
                    for key, value in paper_data.items():
                        if key not in research_study or not research_study[key]:
                            research_study[key] = value

        return {"research_study_list": research_study_list}

    @retrieve_paper_content_timed
    def _search_semantic_scholar(
        self, state: RetrievePaperContentState
    ) -> dict[str, list[dict]]:
        research_study_list = state["research_study_list"]

        for research_study in research_study_list:
            title = research_study.get("title", "")
            if title:
                paper_data = search_ss_by_title(title=title)
                if paper_data:
                    for key, value in paper_data.items():
                        if key not in research_study or not research_study[key]:
                            research_study[key] = value

        return {"research_study_list": research_study_list}

    @retrieve_paper_content_timed
    def _retrieve_text_from_url(
        self, state: RetrievePaperContentState
    ) -> dict[str, list[dict]]:
        research_study_list = state["research_study_list"]

        for research_study in research_study_list:
            # Try to get PDF URL from different fields depending on provider
            pdf_url = (
                research_study.get("pdf_url") or research_study.get("arxiv_url") or ""
            )

            if pdf_url:
                full_text = retrieve_text_from_url(
                    papers_dir=self.papers_dir,
                    pdf_url=pdf_url,
                )
                research_study["full_text"] = full_text

        return {"research_study_list": research_study_list}

    def select_provider(self, state: RetrievePaperContentState) -> str:
        if self.paper_provider == "arxiv":
            return "search_arxiv"
        elif self.paper_provider == "openalex":
            return "search_openalex"
        elif self.paper_provider == "semantic_scholar":
            return "search_semantic_scholar"
        else:
            # Default to arxiv
            return "search_arxiv"

    def build_graph(self) -> CompiledGraph:
        graph_builder = StateGraph(RetrievePaperContentState)
        graph_builder.add_node("search_arxiv", self._search_arxiv)
        graph_builder.add_node("search_openalex", self._search_openalex)
        graph_builder.add_node("search_semantic_scholar", self._search_semantic_scholar)
        graph_builder.add_node("retrieve_text_from_url", self._retrieve_text_from_url)

        graph_builder.add_conditional_edges(
            START,
            self.select_provider,
            {
                "search_arxiv": "search_arxiv",
                "search_openalex": "search_openalex",
                "search_semantic_scholar": "search_semantic_scholar",
            },
        )

        graph_builder.add_edge("search_arxiv", "retrieve_text_from_url")
        graph_builder.add_edge("search_openalex", "retrieve_text_from_url")
        graph_builder.add_edge("search_semantic_scholar", "retrieve_text_from_url")
        graph_builder.add_edge("retrieve_text_from_url", END)
        return graph_builder.compile()


def main():
    save_dir = "/workspaces/airas/data"
    input_data = retrieve_paper_content_subgraph_input_data
    result = RetrievePaperContentSubgraph(
        save_dir=save_dir,
        paper_provider="arxiv",  # Can be "arxiv", "openalex", or "semantic_scholar"
    ).run(input_data)
    print(f"result: {json.dumps(result, indent=2)}")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        logger.error(f"An error occurred: {e}")
        raise
