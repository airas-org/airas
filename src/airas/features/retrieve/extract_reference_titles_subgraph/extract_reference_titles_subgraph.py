import asyncio
import logging

from langgraph.graph import END, START, StateGraph
from langgraph.graph.graph import CompiledGraph
from pydantic import BaseModel
from typing_extensions import TypedDict

from airas.config.llm_config import DEFAULT_NODE_LLMS
from airas.core.base import BaseSubgraph
from airas.features.retrieve.extract_reference_titles_subgraph.input_data import (
    extract_reference_titles_subgraph_input_data,
)
from airas.features.retrieve.extract_reference_titles_subgraph.nodes.extract_reference_titles import (
    extract_reference_titles,
)
from airas.services.api_client.llm_client.llm_facade_client import (
    LLM_MODEL,
    LLMFacadeClient,
)
from airas.types.github import GitHubRepositoryInfo
from airas.types.research_study import ResearchStudy
from airas.utils.execution_timers import ExecutionTimeState, time_node
from airas.utils.logging_utils import setup_logging

setup_logging()
logger = logging.getLogger(__name__)

extract_reference_titles_str = "extract_reference_titles_subgraph"
extract_reference_titles_timed = lambda f: time_node(extract_reference_titles_str)(f)  # noqa: E731


class ExtractReferenceTitlesLLMMapping(BaseModel):
    extract_reference_titles: LLM_MODEL = DEFAULT_NODE_LLMS["extract_reference_titles"]


class ExtractReferenceTitlesInputState(TypedDict):
    research_study_list: list[ResearchStudy]
    github_repository_info: GitHubRepositoryInfo


class ExtractReferenceTitlesHiddenState(TypedDict): ...


class ExtractReferenceTitlesOutputState(TypedDict):
    reference_research_study_list: list[ResearchStudy]


class ExtractReferenceTitlesState(
    ExtractReferenceTitlesInputState,
    ExtractReferenceTitlesHiddenState,
    ExtractReferenceTitlesOutputState,
    ExecutionTimeState,
): ...


class ExtractReferenceTitlesSubgraph(BaseSubgraph):
    InputState = ExtractReferenceTitlesInputState
    OutputState = ExtractReferenceTitlesOutputState

    def __init__(
        self,
        llm_client: LLMFacadeClient,
        llm_mapping: dict[str, str] | ExtractReferenceTitlesLLMMapping | None = None,
        num_reference_paper: int | None = None,
    ):
        if llm_mapping is None:
            self.llm_mapping = ExtractReferenceTitlesLLMMapping()
        elif isinstance(llm_mapping, dict):
            try:
                self.llm_mapping = ExtractReferenceTitlesLLMMapping.model_validate(
                    llm_mapping
                )
            except Exception as e:
                raise TypeError(
                    f"Invalid llm_mapping values. Must contain valid LLM model names. Error: {e}"
                ) from e
        elif isinstance(llm_mapping, ExtractReferenceTitlesLLMMapping):
            self.llm_mapping = llm_mapping
        else:
            raise TypeError(
                f"llm_mapping must be None, dict[str, str], or ExtractReferenceTitlesLLMMapping, "
                f"but got {type(llm_mapping)}"
            )
        self.llm_client = llm_client
        self.num_reference_paper = num_reference_paper

    # TODO: async support
    # @extract_reference_titles_timed
    async def _extract_reference_titles(
        self, state: ExtractReferenceTitlesState
    ) -> dict[str, list[ResearchStudy]]:
        reference_research_study_list = await extract_reference_titles(
            llm_name=self.llm_mapping.extract_reference_titles,
            llm_client=self.llm_client,
            research_study_list=state["research_study_list"],
            github_repository_info=state.get("github_repository_info"),
        )
        if self.num_reference_paper is not None:
            reference_research_study_list = reference_research_study_list[
                : self.num_reference_paper
            ]
        return {"reference_research_study_list": reference_research_study_list}

    def build_graph(self) -> CompiledGraph:
        graph_builder = StateGraph(ExtractReferenceTitlesState)
        graph_builder.add_node(
            "extract_reference_titles", self._extract_reference_titles
        )

        graph_builder.add_edge(START, "extract_reference_titles")
        graph_builder.add_edge("extract_reference_titles", END)

        return graph_builder.compile()


async def main():
    input_data = extract_reference_titles_subgraph_input_data
    result = await ExtractReferenceTitlesSubgraph().arun(input_data)
    print(f"result: {result}")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception as e:
        logger.error(f"An error occurred: {e}")
        raise
