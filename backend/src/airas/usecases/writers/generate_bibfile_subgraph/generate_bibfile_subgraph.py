import logging

from langgraph.graph import END, START, StateGraph
from typing_extensions import TypedDict

from airas.core.execution_timers import ExecutionTimeState, time_node
from airas.core.logging_utils import setup_logging
from airas.core.types.research_study import ResearchStudy
from airas.usecases.writers.generate_bibfile_subgraph.nodes.generate_bibfile import (
    generate_bibfile,
)

setup_logging()
logger = logging.getLogger(__name__)
record_execution_time = lambda f: time_node("generate_bibfile_subgraph")(f)  # noqa: E731


class GenerateBibfileSubgraphInputState(TypedDict):
    research_study_list: list[ResearchStudy]


class GenerateBibfileSubgraphOutputState(ExecutionTimeState):
    references_bib: str


class GenerateBibfileSubgraphState(
    GenerateBibfileSubgraphInputState, GenerateBibfileSubgraphOutputState, total=False
):
    pass


class GenerateBibfileSubgraph:
    def __init__(self):
        pass

    @record_execution_time
    def _generate_bibfile(self, state: GenerateBibfileSubgraphState) -> dict[str, str]:
        references_bib = generate_bibfile(
            research_study_list=state["research_study_list"],
        )
        return {"references_bib": references_bib}

    def build_graph(self):
        graph_builder = StateGraph(
            GenerateBibfileSubgraphState,
            input_schema=GenerateBibfileSubgraphInputState,
            output_schema=GenerateBibfileSubgraphOutputState,
        )
        graph_builder.add_node("generate_bibfile", self._generate_bibfile)

        graph_builder.add_edge(START, "generate_bibfile")
        graph_builder.add_edge("generate_bibfile", END)
        return graph_builder.compile()
