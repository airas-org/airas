import json
import logging
from typing import cast

from langgraph.graph import END, START, StateGraph
from langgraph.graph.graph import CompiledGraph

from airas.core.base import BaseSubgraph
from airas.features.write.writer_subgraph.input_data import (
    writer_subgraph_input_data,
)
from airas.features.write.writer_subgraph.nodes.generate_note import generate_note
from airas.features.write.writer_subgraph.nodes.paper_writing import WritingNode
from airas.services.api_client.llm_client.llm_facade_client import LLM_MODEL
from airas.types.research_hypothesis import ResearchHypothesis
from airas.types.research_study import ResearchStudy
from airas.utils.check_api_key import check_api_key
from airas.utils.execution_timers import ExecutionTimeState, time_node
from airas.utils.logging_utils import setup_logging

setup_logging()
logger = logging.getLogger(__name__)
writer_timed = lambda f: time_node("writer_subgraph")(f)  # noqa: E731


# class WriterSubgraphInputState(TypedDict):
#     base_method_text: str
#     new_method: str
#     verification_policy: str
#     experiment_details: str
#     experiment_code: str
#     output_text_data: str
#     analysis_report: str
#     image_file_name_list: list[str]


# class WriterSubgraphHiddenState(TypedDict):
#     note: str


# class WriterSubgraphOutputState(TypedDict):
#     paper_content: dict[str, str]


class WriterSubgraphState(
    # WriterSubgraphInputState,
    # WriterSubgraphHiddenState,
    # WriterSubgraphOutputState,
    ExecutionTimeState,
):
    base_method_text: str
    new_method: ResearchHypothesis
    generate_paper_data: ResearchStudy


class WriterSubgraph(BaseSubgraph):
    # InputState = WriterSubgraphInputState
    # OutputState = WriterSubgraphOutputState

    def __init__(
        self,
        llm_name: str,
        refine_round: int = 2,
    ):
        self.llm_name = llm_name
        self.refine_round = refine_round
        check_api_key(llm_api_key_check=True)

    @writer_timed
    def _generate_note(self, state: WriterSubgraphState) -> dict:
        new_method = state["new_method"]
        notes = generate_note(
            base_method_text=state["base_method_text"],
            new_method=new_method.method,
            verification_policy=new_method.verification_policy,
            experiment_details=new_method.experiment_details,
            experiment_code=new_method.experiment_code,
            output_text_data=cast(str, new_method.experiment_result.result),
            analysis_report=new_method.experiment_result.analysis_report,
            image_file_name_list=new_method.experiment_result.image_file_name_list,
        )
        new_method.experiment_result.notes = notes
        return {"new_method": new_method}

    @writer_timed
    def _writeup(self, state: WriterSubgraphState) -> dict:
        new_method = state["new_method"]
        paper_content = WritingNode(
            llm_name=cast(LLM_MODEL, self.llm_name),
            refine_round=self.refine_round,
        ).execute(
            note=new_method.experiment_result.notes,
        )
        generate_paper_data = ResearchStudy(
            title=paper_content.title, paper_body=paper_content
        )
        return {"generate_paper_data": generate_paper_data}

    def build_graph(self) -> CompiledGraph:
        graph_builder = StateGraph(WriterSubgraphState)
        graph_builder.add_node("generate_note", self._generate_note)
        graph_builder.add_node("writeup", self._writeup)

        graph_builder.add_edge(START, "generate_note")
        graph_builder.add_edge("generate_note", "writeup")
        graph_builder.add_edge("writeup", END)

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
