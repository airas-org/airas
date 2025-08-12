import json
import logging
from typing import cast

from langgraph.graph import END, START, StateGraph
from langgraph.graph.graph import CompiledGraph
from typing_extensions import TypedDict

from airas.core.base import BaseSubgraph
from airas.features.write.writer_subgraph.input_data import (
    writer_subgraph_input_data,
)
from airas.features.write.writer_subgraph.nodes.generate_note import generate_note
from airas.features.write.writer_subgraph.nodes.refine_paper import refine_paper
from airas.features.write.writer_subgraph.nodes.write_paper import write_paper
from airas.services.api_client.llm_client.llm_facade_client import LLM_MODEL
from airas.types.research_hypothesis import ResearchHypothesis
from airas.types.research_study import ResearchStudy
from airas.utils.check_api_key import check_api_key
from airas.utils.execution_timers import ExecutionTimeState, time_node
from airas.utils.logging_utils import setup_logging

setup_logging()
logger = logging.getLogger(__name__)
writer_timed = lambda f: time_node("writer_subgraph")(f)  # noqa: E731


class WriterSubgraphInputState(TypedDict):
    new_method: ResearchHypothesis
    research_study_list: list[ResearchStudy]
    reference_research_study_list: list[ResearchStudy]
    references_bib: str
    # TODO: Enriching refenrence candidate information


class WriterSubgraphHiddenState(TypedDict):
    note: str
    refinement_count: int


class WriterSubgraphOutputState(TypedDict):
    paper_content: dict[str, str]


class WriterSubgraphState(
    WriterSubgraphInputState,
    WriterSubgraphHiddenState,
    WriterSubgraphOutputState,
    ExecutionTimeState,
):
    pass


class WriterSubgraph(BaseSubgraph):
    InputState = WriterSubgraphInputState
    OutputState = WriterSubgraphOutputState

    def __init__(
        self,
        llm_name: LLM_MODEL,
        max_refinement_count: int = 2,
    ):
        self.llm_name = llm_name
        self.max_refinement_count = max_refinement_count
        check_api_key(llm_api_key_check=True)

    @writer_timed
    def _initialize(self, state: WriterSubgraphState) -> dict:
        return {
            "refinement_count": 0,
        }

    @writer_timed
    def _generate_note(self, state: WriterSubgraphState) -> dict:
        note = generate_note(
            new_method=state["new_method"],
            research_study_list=state["research_study_list"],
            reference_research_study_list=state["reference_research_study_list"],
            references_bib=state["references_bib"],
        )
        return {"note": note}

    @writer_timed
    def _write_paper(self, state: WriterSubgraphState) -> dict:
        paper_content = write_paper(
            llm_name=cast(LLM_MODEL, self.llm_name),
            note=state["note"],
        )
        return {"paper_content": paper_content}

    @writer_timed
    def _refine_paper(self, state: WriterSubgraphState) -> dict:
        paper_content = refine_paper(
            llm_name=cast(LLM_MODEL, self.llm_name),
            paper_content=state["paper_content"],
            note=state["note"],
        )
        return {
            "paper_content": paper_content,
            "refinement_count": state["refinement_count"] + 1,
        }

    @writer_timed
    def should_finish_refinement(self, state: WriterSubgraphState) -> str:
        if state["refinement_count"] >= self.max_refinement_count:
            return "end"
        return "refine"

    def build_graph(self) -> CompiledGraph:
        graph_builder = StateGraph(WriterSubgraphState)
        graph_builder.add_node("initialize", self._initialize)
        graph_builder.add_node("generate_note", self._generate_note)
        graph_builder.add_node("write_paper", self._write_paper)
        graph_builder.add_node("refine_paper", self._refine_paper)

        graph_builder.add_edge(START, "initialize")
        graph_builder.add_edge("initialize", "generate_note")
        graph_builder.add_edge("generate_note", "write_paper")
        graph_builder.add_conditional_edges(
            "write_paper",
            self.should_finish_refinement,
            {"end": END, "refine": "refine_paper"},
        )
        graph_builder.add_conditional_edges(
            "refine_paper",
            self.should_finish_refinement,
            {"end": END, "refine": "refine_paper"},
        )

        return graph_builder.compile()


def main():
    llm_name = "o3-mini-2025-01-31"
    refine_round = 1
    input = writer_subgraph_input_data

    result = WriterSubgraph(
        llm_name=llm_name,
        max_refinement_count=refine_round,
    ).run(input)
    print(f"result: {json.dumps(result, indent=2)}")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        logger.error(f"Error running WriterSubgraph: {e}")
        raise
