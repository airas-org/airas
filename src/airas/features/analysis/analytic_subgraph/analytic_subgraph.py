import json
import logging
from typing import cast

from langgraph.graph import END, START, StateGraph
from langgraph.graph.graph import CompiledGraph

# from typing_extensions import TypedDict
from airas.core.base import BaseSubgraph
from airas.features.analysis.analytic_subgraph.input_data import (
    analytic_subgraph_input_data,
)
from airas.features.analysis.analytic_subgraph.nodes.analytic_node import analytic_node
from airas.services.api_client.llm_client.llm_facade_client import LLM_MODEL
from airas.types.method import MLMethodData
from airas.utils.check_api_key import check_api_key
from airas.utils.execution_timers import ExecutionTimeState, time_node
from airas.utils.logging_utils import setup_logging

setup_logging()
logger = logging.getLogger(__name__)

analytic_timed = lambda f: time_node("analytic_subgraph")(f)  # noqa: E731


# class AnalyticSubgraphInputState(TypedDict):
#     new_method: str
#     verification_policy: str
#     experiment_code: str
#     output_text_data: str


# class AnalyticSubgraphHiddenState(TypedDict):
#     pass


# class AnalyticSubgraphOutputState(TypedDict):
#     analysis_report: str


class AnalyticSubgraphState(
    # AnalyticSubgraphInputState,
    # AnalyticSubgraphHiddenState,
    # AnalyticSubgraphOutputState,
    ExecutionTimeState,
):
    new_method: MLMethodData


class AnalyticSubgraph(BaseSubgraph):
    # InputState = AnalyticSubgraphInputState
    # OutputState = AnalyticSubgraphOutputState

    def __init__(
        self,
        llm_name: LLM_MODEL,
    ):
        self.llm_name = llm_name
        check_api_key(llm_api_key_check=True)

    @analytic_timed
    def _analytic_node(self, state: AnalyticSubgraphState) -> dict:
        new_method = state["new_method"]
        analysis_report = analytic_node(
            llm_name=cast(LLM_MODEL, self.llm_name),
            new_method=new_method.method,
            verification_policy=new_method.verification_policy,
            experiment_code=new_method.experiment_code,
            output_text_data=new_method.experiment_result.result,
        )
        new_method.experiment_result.analysis_report = analysis_report
        return {"new_method": new_method}

    def build_graph(self) -> CompiledGraph:
        graph_builder = StateGraph(AnalyticSubgraphState)
        graph_builder.add_node("analytic_node", self._analytic_node)

        graph_builder.add_edge(START, "analytic_node")
        graph_builder.add_edge("analytic_node", END)
        return graph_builder.compile()


def main():
    llm_name = "o3-mini-2025-01-31"
    input = analytic_subgraph_input_data

    result = AnalyticSubgraph(
        llm_name=llm_name,
    ).run(input)

    print(f"result: {json.dumps(result, indent=2)}")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        logger.error(f"Error running AnalyticSubgraph: {e}")
        raise
