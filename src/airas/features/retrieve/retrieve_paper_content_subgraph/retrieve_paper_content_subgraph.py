import json
import logging
import os
from typing import Literal

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
from airas.features.retrieve.retrieve_paper_content_subgraph.nodes.search_arxiv_by_id import (
    search_arxiv_by_id,
)
from airas.features.retrieve.retrieve_paper_content_subgraph.nodes.search_arxiv_id_from_title import (
    search_arxiv_id_from_title,
)
from airas.features.retrieve.retrieve_paper_content_subgraph.nodes.search_ss_by_id import (
    search_ss_by_id,
)
from airas.features.retrieve.retrieve_paper_content_subgraph.prompt.openai_websearch_arxiv_ids_prompt import (
    openai_websearch_arxiv_ids_prompt,
)
from airas.utils.execution_timers import ExecutionTimeState, time_node
from airas.utils.logging_utils import setup_logging

setup_logging()
logger = logging.getLogger(__name__)

retrieve_paper_content_str = "retrieve_paper_content_subgraph"
retrieve_paper_content_timed = lambda f: time_node(retrieve_paper_content_str)(f)  # noqa: E731


class RetrievePaperContentInputState(TypedDict, total=False):
    research_study_list: list[dict]
    reference_research_study_list: list[dict]


class RetrievePaperContentHiddenState(TypedDict):
    temp_research_study_list: list[dict]


class RetrievePaperContentOutputState(TypedDict, total=False):
    research_study_list: list[dict]
    reference_research_study_list: list[dict]


class RetrievePaperContentState(
    RetrievePaperContentInputState,
    RetrievePaperContentHiddenState,
    RetrievePaperContentOutputState,
    ExecutionTimeState,
    total=False,
): ...


UsedStudyListSource = Literal["research_study_list", "reference_research_study_list"]


class RetrievePaperContentSubgraph(BaseSubgraph):
    InputState = RetrievePaperContentInputState
    OutputState = RetrievePaperContentOutputState

    def __init__(
        self,
        save_dir: str,
        target_study_list_source: UsedStudyListSource,
        paper_provider: str = "arxiv",
    ):
        self.save_dir = save_dir
        self.papers_dir = os.path.join(self.save_dir, "papers")
        self.paper_provider = paper_provider
        self.target_study_list_source = target_study_list_source
        os.makedirs(self.papers_dir, exist_ok=True)

    @retrieve_paper_content_timed
    def _initialize(self, state: RetrievePaperContentState) -> dict:
        if self.target_study_list_source == "research_study_list":
            research_study_list = state["research_study_list"]
        elif self.target_study_list_source == "reference_research_study_list":
            research_study_list = state["reference_research_study_list"]
        else:
            raise ValueError("No research study list found in the state.")
        return {"temp_research_study_list": research_study_list}

    @retrieve_paper_content_timed
    def _search_arxiv_id_from_title(self, state: RetrievePaperContentState) -> dict:
        research_study_list = state["temp_research_study_list"]

        for research_study in research_study_list:
            title = research_study.get("title", "")
            arxiv_id = search_arxiv_id_from_title(
                llm_name="gpt-4o-2024-11-20",
                prompt_template=openai_websearch_arxiv_ids_prompt,
                title=title,
            )
            research_study["arxiv_id"] = arxiv_id

        return {"temp_research_study_list": research_study_list}

    @retrieve_paper_content_timed
    def _search_arxiv_by_id(self, state: RetrievePaperContentState) -> dict:
        research_study_list = state["temp_research_study_list"]

        for research_study in research_study_list:
            if arxiv_id := research_study.get("arxiv_id", ""):
                arxiv_info = search_arxiv_by_id(arxiv_id)

                if arxiv_info:
                    if "external_sources" not in research_study:
                        research_study["external_sources"] = {}
                    research_study["external_sources"]["arxiv_info"] = arxiv_info

                    if arxiv_info.get("summary"):
                        research_study["abstract"] = arxiv_info["summary"]

                    if "meta_data" not in research_study:
                        research_study["meta_data"] = {}

                    for key, value in arxiv_info.items():
                        if key not in ["title", "summary"]:
                            research_study["meta_data"][key] = (
                                value  #  TODO: Match the structure of MetaData
                            )

        return {"temp_research_study_list": research_study_list}

    @retrieve_paper_content_timed
    def _search_ss_by_id(
        self, state: RetrievePaperContentState
    ) -> dict[str, list[dict]]:
        research_study_list = state["temp_research_study_list"]

        for research_study in research_study_list:
            if arxiv_id := research_study.get("arxiv_id", ""):
                semantic_scholar_info = search_ss_by_id(arxiv_id)

                if semantic_scholar_info:
                    if "external_sources" not in research_study:
                        research_study["external_sources"] = {}
                    research_study["external_sources"]["semantic_scholar_info"] = (
                        semantic_scholar_info
                    )

                    if semantic_scholar_info.get("abstract"):
                        research_study["abstract"] = semantic_scholar_info["abstract"]

                    if "meta_data" not in research_study:
                        research_study["meta_data"] = {}

                    for key, value in semantic_scholar_info.items():
                        if key not in ["title", "abstract"]:
                            research_study["meta_data"][key] = (
                                value  #  TODO: Match the structure of MetaData
                            )

        return {"temp_research_study_list": research_study_list}

    @retrieve_paper_content_timed
    def _retrieve_text_from_url(
        self, state: RetrievePaperContentState
    ) -> dict[str, list[dict]]:
        research_study_list = state["temp_research_study_list"]

        for research_study in research_study_list:
            if arxiv_url := research_study.get("arxiv_url", ""):
                full_text = retrieve_text_from_url(
                    papers_dir=self.papers_dir,
                    pdf_url=arxiv_url,
                )
                research_study["full_text"] = full_text

        return {"temp_research_study_list": research_study_list}

    def select_provider(self, state: RetrievePaperContentState) -> str:
        if self.paper_provider == "semantic_scholar":
            return "search_ss_by_id"
        else:
            return "search_arxiv_by_id"

    @retrieve_paper_content_timed
    def _format_output(self, state: RetrievePaperContentState) -> dict:
        if self.target_study_list_source == "research_study_list":
            return {
                "research_study_list": state["temp_research_study_list"],
            }
        else:
            return {
                "reference_research_study_list": state["temp_research_study_list"],
            }

    def build_graph(self) -> CompiledGraph:
        graph_builder = StateGraph(RetrievePaperContentState)
        graph_builder.add_node("initialize", self._initialize)
        graph_builder.add_node(
            "search_arxiv_id_from_title", self._search_arxiv_id_from_title
        )
        graph_builder.add_node("search_arxiv_by_id", self._search_arxiv_by_id)
        graph_builder.add_node("search_ss_by_id", self._search_ss_by_id)
        graph_builder.add_node("retrieve_text_from_url", self._retrieve_text_from_url)
        graph_builder.add_node("format_output", self._format_output)

        graph_builder.add_edge(START, "initialize")
        graph_builder.add_edge("initialize", "search_arxiv_id_from_title")
        graph_builder.add_conditional_edges(
            "search_arxiv_id_from_title",
            self.select_provider,
            {
                "search_arxiv_by_id": "search_arxiv_by_id",
                "search_ss_by_id": "search_ss_by_id",
            },
        )
        graph_builder.add_edge("search_arxiv_by_id", "retrieve_text_from_url")
        graph_builder.add_edge("search_ss_by_id", "retrieve_text_from_url")
        graph_builder.add_edge("retrieve_text_from_url", "format_output")
        graph_builder.add_edge("format_output", END)
        return graph_builder.compile()


def main():
    save_dir = "/workspaces/airas/data"
    input_data = retrieve_paper_content_subgraph_input_data
    result = RetrievePaperContentSubgraph(
        save_dir=save_dir,
        target_study_list_source="research_study_list",
        paper_provider="arxiv",  # Can be "arxiv" or "semantic_scholar"
    ).run(input_data)
    print(f"result: {json.dumps(result, indent=2)}")

    research_study_list = result.get("research_study_list", [])

    for i, study in enumerate(research_study_list):
        title = study.get("title", "No Title Found")
        arxiv_url = study.get("arxiv_url", "No arXiv URL Found")

        print(f"\nPaper {i + 1}:")
        print(f"  Title: {title}")
        print(f"  arXiv URL: {arxiv_url}")

    print("\n---------------------------------")
    print("Process finished.")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        logger.error(f"An error occurred: {e}")
        raise
