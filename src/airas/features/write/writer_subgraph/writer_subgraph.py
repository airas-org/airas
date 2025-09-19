import logging

from langgraph.graph import END, START, StateGraph
from langgraph.graph.graph import CompiledGraph
from pydantic import BaseModel
from typing_extensions import TypedDict

from airas.config.llm_config import DEFAULT_NODE_LLMS
from airas.core.base import BaseSubgraph
from airas.features.write.writer_subgraph.input_data import (
    writer_subgraph_input_data,
)
from airas.features.write.writer_subgraph.nodes.generate_note import generate_note
from airas.features.write.writer_subgraph.nodes.refine_paper import refine_paper
from airas.features.write.writer_subgraph.nodes.write_paper import write_paper
from airas.services.api_client.llm_client.llm_facade_client import LLM_MODEL
from airas.types.github import GitHubRepositoryInfo
from airas.types.paper import PaperContent
from airas.types.research_hypothesis import ResearchHypothesis
from airas.types.research_study import ResearchStudy
from airas.utils.check_api_key import check_api_key
from airas.utils.execution_timers import ExecutionTimeState, time_node
from airas.utils.logging_utils import setup_logging

setup_logging()
logger = logging.getLogger(__name__)
writer_timed = lambda f: time_node("writer_subgraph")(f)  # noqa: E731


class WriterLLMMapping(BaseModel):
    write_paper: LLM_MODEL = DEFAULT_NODE_LLMS["write_paper"]
    refine_paper: LLM_MODEL = DEFAULT_NODE_LLMS["refine_paper"]


class WriterSubgraphInputState(TypedDict):
    new_method: ResearchHypothesis
    research_study_list: list[ResearchStudy]
    reference_research_study_list: list[ResearchStudy]
    references_bib: str
    # TODO: Enriching refenrence candidate information
    github_repository_info: GitHubRepositoryInfo


class WriterSubgraphHiddenState(TypedDict):
    note: str
    refinement_count: int


class WriterSubgraphOutputState(TypedDict):
    paper_content: PaperContent


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
        llm_mapping: dict[str, str] | WriterLLMMapping | None = None,
        writing_refinement_rounds: int = 2,
    ):
        if llm_mapping is None:
            self.llm_mapping = WriterLLMMapping()
        elif isinstance(llm_mapping, dict):
            self.llm_mapping = WriterLLMMapping(**llm_mapping)
        elif isinstance(llm_mapping, WriterLLMMapping):
            # すでに型が正しい場合も受け入れる
            self.llm_mapping = llm_mapping
        else:
            raise TypeError(
                f"llm_mapping must be None, dict[str, str], or WriterLLMMapping, "
                f"but got {type(llm_mapping)}"
            )
        self.writing_refinement_rounds = writing_refinement_rounds
        check_api_key(llm_api_key_check=True)

    @writer_timed
    def _initialize(self, state: WriterSubgraphState) -> dict[str, int]:
        return {
            "refinement_count": 0,
        }

    @writer_timed
    def _generate_note(self, state: WriterSubgraphState) -> dict[str, str]:
        note = generate_note(
            new_method=state["new_method"],
            research_study_list=state["research_study_list"],
            reference_research_study_list=state["reference_research_study_list"],
            references_bib=state["references_bib"],
        )
        return {"note": note}

    @writer_timed
    def _write_paper(self, state: WriterSubgraphState) -> dict[str, PaperContent]:
        paper_content = write_paper(
            llm_name=self.llm_mapping.write_paper,
            note=state["note"],
        )
        return {"paper_content": paper_content}

    @writer_timed
    def _refine_paper(
        self, state: WriterSubgraphState
    ) -> dict[str, PaperContent | int]:
        paper_content = refine_paper(
            llm_name=self.llm_mapping.refine_paper,
            paper_content=state["paper_content"],
            note=state["note"],
        )
        return {
            "paper_content": paper_content,
            "refinement_count": state["refinement_count"] + 1,
        }

    @writer_timed
    def should_finish_refinement(self, state: WriterSubgraphState) -> str:
        if state["refinement_count"] >= self.writing_refinement_rounds:
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
    refine_round = 1
    input = writer_subgraph_input_data

    result = WriterSubgraph(
        writing_refinement_rounds=refine_round,
    ).run(input)
    print(f"result: {result}")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        logger.error(f"Error running WriterSubgraph: {e}")
        raise
