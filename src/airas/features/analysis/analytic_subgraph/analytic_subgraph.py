import logging

from langgraph.graph import END, START, StateGraph
from langgraph.graph.graph import CompiledGraph
from pydantic import BaseModel
from typing_extensions import TypedDict

from airas.config.llm_config import DEFAULT_NODE_LLMS
from airas.core.base import BaseSubgraph
from airas.features.analysis.analytic_subgraph.input_data import (
    analytic_subgraph_input_data,
)
from airas.features.analysis.analytic_subgraph.nodes.analytic_node import analytic_node
from airas.services.api_client.llm_client.llm_facade_client import LLM_MODEL
from airas.types.research_hypothesis import ExperimentalAnalysis, ResearchHypothesis
from airas.utils.check_api_key import check_api_key
from airas.utils.execution_timers import ExecutionTimeState, time_node
from airas.utils.logging_utils import setup_logging

setup_logging()
logger = logging.getLogger(__name__)

analytic_timed = lambda f: time_node("analytic_subgraph")(f)  # noqa: E731


class AnalyticLLMMapping(BaseModel):
    analytic_node: LLM_MODEL = DEFAULT_NODE_LLMS["analytic_node"]


class AnalyticSubgraphInputState(TypedDict):
    new_method: ResearchHypothesis


class AnalyticSubgraphHiddenState(TypedDict):
    pass


class AnalyticSubgraphOutputState(TypedDict):
    analysis_report: str


class AnalyticSubgraphState(
    AnalyticSubgraphInputState,
    AnalyticSubgraphHiddenState,
    AnalyticSubgraphOutputState,
    ExecutionTimeState,
):
    pass


class AnalyticSubgraph(BaseSubgraph):
    InputState = AnalyticSubgraphInputState
    OutputState = AnalyticSubgraphOutputState

    def __init__(
        self,
        llm_mapping: AnalyticLLMMapping | None = None,
    ):
        self.llm_mapping = llm_mapping or AnalyticLLMMapping()
        check_api_key(llm_api_key_check=True)

    @analytic_timed
    def _analytic_node(self, state: AnalyticSubgraphState) -> dict:
        new_method = state["new_method"]
        analysis_report = analytic_node(
            llm_name=self.llm_mapping.analytic_node,
            new_method=new_method,
        )
        new_method.experimental_analysis = ExperimentalAnalysis(
            analysis_report=analysis_report
        )
        return {"new_method": new_method}

    def build_graph(self) -> CompiledGraph:
        graph_builder = StateGraph(AnalyticSubgraphState)
        graph_builder.add_node("analytic_node", self._analytic_node)

        graph_builder.add_edge(START, "analytic_node")
        graph_builder.add_edge("analytic_node", END)
        return graph_builder.compile()


def main():
    input = analytic_subgraph_input_data

    result = AnalyticSubgraph().run(input)

    print(f"result: {result}")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        logger.error(f"Error running AnalyticSubgraph: {e}")
        raise
