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
from airas.features.write.writer_subgraph.nodes.refine import refine
from airas.features.write.writer_subgraph.nodes.write import write
from airas.services.api_client.llm_client.llm_facade_client import LLM_MODEL
from airas.utils.check_api_key import check_api_key
from airas.utils.execution_timers import ExecutionTimeState, time_node
from airas.utils.logging_utils import setup_logging

setup_logging()
logger = logging.getLogger(__name__)
writer_timed = lambda f: time_node("writer_subgraph")(f)  # noqa: E731


class WriterSubgraphInputState(TypedDict):
    research_hypothesis: dict
    references_bib: str
    # TODO: Enriching refenrence candidate information


class WriterSubgraphHiddenState(TypedDict):
    note: str


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
        refine_round: int = 2,
    ):
        self.llm_name = llm_name
        self.refine_round = refine_round
        check_api_key(llm_api_key_check=True)

    @writer_timed
    def _generate_note(self, state: WriterSubgraphState) -> dict:
        note = generate_note(
            research_hypothesis=state["research_hypothesis"],
            references_bib=state["references_bib"],
        )
        return {"note": note}

    @writer_timed
    def _write(self, state: WriterSubgraphState) -> dict:
        paper_content = write(
            llm_name=cast(LLM_MODEL, self.llm_name),
            note=state["note"],
        )
        return {"paper_content": paper_content}

    @writer_timed
    def _refine(self, state: WriterSubgraphState) -> dict:
        paper_content = refine(
            llm_name=cast(LLM_MODEL, self.llm_name),
            paper_content=state["paper_content"],
            note=state["note"],
        )
        return {"paper_content": paper_content}

    def build_graph(self) -> CompiledGraph:
        graph_builder = StateGraph(WriterSubgraphState)
        graph_builder.add_node("generate_note", self._generate_note)
        graph_builder.add_node("write", self._write)
        for i in range(self.refine_round):
            graph_builder.add_node(f"refine_{i + 1}", self._refine)

        graph_builder.add_edge(START, "generate_note")
        graph_builder.add_edge("generate_note", "write")
        graph_builder.add_edge("write", "refine_1")
        for i in range(1, self.refine_round):
            graph_builder.add_edge(f"refine_{i}", f"refine_{i + 1}")
        graph_builder.add_edge(f"refine_{self.refine_round}", END)

        return graph_builder.compile()


def main():
    llm_name = "o3-mini-2025-01-31"
    refine_round = 1
    input = writer_subgraph_input_data

    result = WriterSubgraph(
        llm_name=llm_name,
        refine_round=refine_round,
    ).run(input)
    print(f"result: {json.dumps(result, indent=2)}")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        logger.error(f"Error running WriterSubgraph: {e}")
        raise
