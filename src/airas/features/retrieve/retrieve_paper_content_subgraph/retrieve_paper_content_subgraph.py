import logging
from typing import Literal

from langgraph.graph import END, START, StateGraph
from langgraph.graph.graph import CompiledGraph
from pydantic import BaseModel
from typing_extensions import TypedDict

from airas.config.llm_config import DEFAULT_NODE_LLMS
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
from airas.services.api_client.llm_client.llm_facade_client import LLM_MODEL
from airas.types.research_study import ResearchStudy
from airas.utils.execution_timers import ExecutionTimeState, time_node
from airas.utils.logging_utils import setup_logging

setup_logging()
logger = logging.getLogger(__name__)

retrieve_paper_content_str = "retrieve_paper_content_subgraph"
retrieve_paper_content_timed = lambda f: time_node(retrieve_paper_content_str)(f)  # noqa: E731


class RetrievePaperContentLLMMapping(BaseModel):
    search_arxiv_id_from_title: LLM_MODEL = DEFAULT_NODE_LLMS[
        "search_arxiv_id_from_title"
    ]


class RetrievePaperContentInputState(TypedDict, total=False):
    research_study_list: list[ResearchStudy]
    reference_research_study_list: list[ResearchStudy]


class RetrievePaperContentHiddenState(TypedDict):
    tmp_research_study_list: list[ResearchStudy]


class RetrievePaperContentOutputState(TypedDict, total=False):
    research_study_list: list[ResearchStudy]
    reference_research_study_list: list[ResearchStudy]


class RetrievePaperContentState(
    RetrievePaperContentInputState,
    RetrievePaperContentHiddenState,
    RetrievePaperContentOutputState,
    ExecutionTimeState,
    total=False,
): ...


UsedStudyListSource = Literal["research_study_list", "reference_research_study_list"]


# TODO:Handle cases where there are too many citation candidates.
class RetrievePaperContentSubgraph(BaseSubgraph):
    InputState = RetrievePaperContentInputState
    OutputState = RetrievePaperContentOutputState

    def __init__(
        self,
        target_study_list_source: UsedStudyListSource,
        llm_mapping: dict[str, str] | RetrievePaperContentLLMMapping | None = None,
        # TODO: Literal["arxiv", "semantic_scholar"]の実装に変更する
        paper_provider: str = "arxiv",
    ):
        if llm_mapping is None:
            self.llm_mapping = RetrievePaperContentLLMMapping()
        elif isinstance(llm_mapping, dict):
            try:
                self.llm_mapping = RetrievePaperContentLLMMapping.model_validate(
                    llm_mapping
                )
            except Exception as e:
                raise TypeError(
                    f"Invalid llm_mapping values. Must contain valid LLM model names. Error: {e}"
                ) from e
        elif isinstance(llm_mapping, RetrievePaperContentLLMMapping):
            self.llm_mapping = llm_mapping
        else:
            raise TypeError(
                f"llm_mapping must be None, dict[str, str], or RetrievePaperContentLLMMapping, "
                f"but got {type(llm_mapping)}"
            )
        self.paper_provider = paper_provider
        self.target_study_list_source = target_study_list_source

    @retrieve_paper_content_timed
    def _initialize(
        self, state: RetrievePaperContentState
    ) -> dict[str, list[ResearchStudy]]:
        if self.target_study_list_source == "research_study_list":
            research_study_list = state["research_study_list"]
        elif self.target_study_list_source == "reference_research_study_list":
            research_study_list = state["reference_research_study_list"]
            if len(research_study_list) >= 30:
                logger.warning(
                    f"{len(research_study_list)} reference research studies found, limiting to 30 for processing."
                )
                research_study_list = research_study_list[:30]
        else:
            raise ValueError("No research study list found in the state.")
        return {"tmp_research_study_list": research_study_list}

    @retrieve_paper_content_timed
    def _search_arxiv_id_from_title(
        self, state: RetrievePaperContentState
    ) -> dict[str, list[ResearchStudy]]:
        research_study_list = state["tmp_research_study_list"]

        research_study_list = search_arxiv_id_from_title(
            llm_name=self.llm_mapping.search_arxiv_id_from_title,
            prompt_template=openai_websearch_arxiv_ids_prompt,
            research_study_list=research_study_list,
        )
        return {"tmp_research_study_list": research_study_list}

    @retrieve_paper_content_timed
    def _search_arxiv_by_id(
        self, state: RetrievePaperContentState
    ) -> dict[str, list[ResearchStudy]]:
        research_study_list = state["tmp_research_study_list"]

        research_study_list = search_arxiv_by_id(research_study_list)
        return {"tmp_research_study_list": research_study_list}

    @retrieve_paper_content_timed
    def _search_ss_by_id(
        self, state: RetrievePaperContentState
    ) -> dict[str, list[ResearchStudy]]:
        research_study_list = state["tmp_research_study_list"]

        research_study_list = search_ss_by_id(research_study_list)
        return {"tmp_research_study_list": research_study_list}

    @retrieve_paper_content_timed
    def _retrieve_text_from_url(
        self, state: RetrievePaperContentState
    ) -> dict[str, list[ResearchStudy]]:
        research_study_list = state["tmp_research_study_list"]

        research_study_list = retrieve_text_from_url(
            research_study_list=research_study_list,
        )
        return {"tmp_research_study_list": research_study_list}

    def select_provider(self, state: RetrievePaperContentState) -> str:
        if self.paper_provider == "semantic_scholar":
            return "search_ss_by_id"
        else:
            return "search_arxiv_by_id"

    @retrieve_paper_content_timed
    def _format_output(self, state: RetrievePaperContentState) -> list[ResearchStudy]:
        if self.target_study_list_source == "research_study_list":
            return {
                "research_study_list": state["tmp_research_study_list"],
            }
        else:
            return {
                "reference_research_study_list": state["tmp_research_study_list"],
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
    input_data = retrieve_paper_content_subgraph_input_data
    result = RetrievePaperContentSubgraph(
        target_study_list_source="research_study_list",
        paper_provider="arxiv",  # Can be "arxiv" or "semantic_scholar"
    ).run(input_data)
    print(f"result: {result}")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        logger.error(f"An error occurred: {e}")
        raise
