import logging
import os

from langgraph.graph import END, START, StateGraph
from langgraph.graph.graph import CompiledGraph
from typing_extensions import TypedDict

from airas.utils.check_api_key import check_api_key
from airas.utils.execution_timers import ExecutionTimeState, time_node
from airas.utils.github_utils.graph_wrapper import create_wrapped_subgraph
from airas.utils.logging_utils import setup_logging
from airas.write.writer_subgraph.input_data import (
    writer_subgraph_input_data,
)
from airas.write.writer_subgraph.nodes.generate_note import generate_note
from airas.write.writer_subgraph.nodes.paper_writing import WritingNode

setup_logging()
logger = logging.getLogger(__name__)

class WriterSubgraphInputState(TypedDict):
    base_method_text: str
    new_method: str
    verification_policy: str
    experiment_details: str
    experiment_code: str
    output_text_data: str
    analysis_report: str


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


class WriterSubgraph:
    def __init__(
        self,
        save_dir: str,
        llm_name: str,
        refine_round: int = 4,
    ):
        self.save_dir = save_dir
        self.llm_name = llm_name
        self.refine_round = refine_round
        self.figures_dir = os.path.join(self.save_dir, "images")
        os.makedirs(self.figures_dir, exist_ok=True)
        check_api_key(llm_api_key_check=True)

    @time_node("writer_subgraph", "_generate_note_node")
    def _generate_note_node(self, state: WriterSubgraphState) -> dict:
        logger.info("---WriterSubgraph---")
        note = generate_note(state=dict(state), figures_dir=self.figures_dir)
        return {"note": note}

    @time_node("writer_subgraph", "_writeup_node")
    def _writeup_node(self, state: WriterSubgraphState) -> dict:
        paper_content = WritingNode(
            llm_name=self.llm_name,
            refine_round=self.refine_round,
        ).execute(
            note=state["note"],
        )
        return {"paper_content": paper_content}

    def build_graph(self) -> CompiledGraph:
        graph_builder = StateGraph(WriterSubgraphState)
        # make nodes
        graph_builder.add_node("generate_note_node", self._generate_note_node)
        graph_builder.add_node("writeup_node", self._writeup_node)
        # make edges
        graph_builder.add_edge(START, "generate_note_node")
        graph_builder.add_edge("generate_note_node", "writeup_node")
        graph_builder.add_edge("writeup_node", END)

        return graph_builder.compile()


PaperWrite = create_wrapped_subgraph(
    WriterSubgraph, WriterSubgraphInputState, WriterSubgraphOutputState
)


if __name__ == "__main__":
    llm_name = "o3-mini-2025-01-31"
    save_dir = "/workspaces/researchgraph/data"
    refine_round = 1

    github_repository = "auto-res2/experiment_script_matsuzawa"
    branch_name = "base-branch"

    subgraph = WriterSubgraph(
        save_dir=save_dir,
        llm_name=llm_name,
        refine_round=refine_round,
    ).build_graph()

    output = subgraph.invoke(writer_subgraph_input_data)
    print(f"output: {output}")

    # paper_writer = PaperWriter(
    #     github_repository=github_repository,
    #     branch_name=branch_name,
    #     llm_name=llm_name,
    #     save_dir=save_dir,
    #     refine_round=refine_round,
    # )

    # result = paper_writer.run({})
    # print(f"result: {result}")
