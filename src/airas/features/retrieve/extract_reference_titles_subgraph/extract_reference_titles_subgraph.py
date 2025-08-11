import logging

from langgraph.graph import END, START, StateGraph
from langgraph.graph.graph import CompiledGraph
from typing_extensions import TypedDict

from airas.core.base import BaseSubgraph
from airas.features.retrieve.extract_reference_titles_subgraph.input_data import (
    extract_reference_titles_subgraph_input_data,
)
from airas.features.retrieve.extract_reference_titles_subgraph.nodes.extract_reference_titles import (
    extract_reference_titles,
)
from airas.services.api_client.llm_client.llm_facade_client import (
    LLM_MODEL,
)
from airas.types.research_study import ResearchStudy
from airas.utils.execution_timers import ExecutionTimeState, time_node
from airas.utils.logging_utils import setup_logging

setup_logging()
logger = logging.getLogger(__name__)

extract_reference_titles_str = "extract_reference_titles_subgraph"
extract_reference_titles_timed = lambda f: time_node(extract_reference_titles_str)(f)  # noqa: E731


class ExtractReferenceTitlesInputState(TypedDict):
    research_study_list: list[ResearchStudy]


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
        llm_name: LLM_MODEL,
    ):
        self.llm_name = llm_name

    @extract_reference_titles_timed
    def _extract_reference_titles(
        self, state: ExtractReferenceTitlesState
    ) -> dict[str, list[ResearchStudy]]:
        reference_research_study_list = extract_reference_titles(
            llm_name=self.llm_name,
            research_study_list=state["research_study_list"],
        )
        return {"reference_research_study_list": reference_research_study_list}

    def build_graph(self) -> CompiledGraph:
        graph_builder = StateGraph(ExtractReferenceTitlesState)
        graph_builder.add_node(
            "extract_reference_titles", self._extract_reference_titles
        )

        graph_builder.add_edge(START, "extract_reference_titles")
        graph_builder.add_edge("extract_reference_titles", END)

        return graph_builder.compile()


def main():
    input_data = extract_reference_titles_subgraph_input_data
    result = ExtractReferenceTitlesSubgraph(
        llm_name="gemini-2.0-flash-001",
    ).run(input_data)
    print(f"result: {result}")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        logger.error(f"An error occurred: {e}")
        raise
