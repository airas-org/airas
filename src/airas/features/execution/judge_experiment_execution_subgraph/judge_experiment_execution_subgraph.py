import logging
from typing import Any

from langgraph.graph import END, START, StateGraph
from langgraph.graph.graph import CompiledGraph
from pydantic import BaseModel
from typing_extensions import TypedDict

from airas.config.llm_config import DEFAULT_NODE_LLMS
from airas.core.base import BaseSubgraph
from airas.features.execution.judge_experiment_execution_subgraph.nodes.should_fix_code import (
    should_fix_code,
)
from airas.services.api_client.llm_client.llm_facade_client import LLM_MODEL
from airas.types.research_hypothesis import ResearchHypothesis
from airas.utils.check_api_key import check_api_key
from airas.utils.execution_timers import ExecutionTimeState, time_node
from airas.utils.logging_utils import setup_logging

setup_logging()
logger = logging.getLogger(__name__)


def judge_experiment_execution_timed(f):
    return time_node("judge_experiment_execution_subgraph")(f)  # noqa: E731


class JudgeExperimentExecutionLLMMapping(BaseModel):
    should_fix_code: LLM_MODEL = DEFAULT_NODE_LLMS["should_fix_code"]


class JudgeExperimentExecutionSubgraphInputState(TypedDict):
    new_method: ResearchHypothesis
    executed_flag: bool


class JudgeExperimentExecutionSubgraphHiddenState(TypedDict): ...


class JudgeExperimentExecutionSubgraphOutputState(TypedDict):
    is_experiment_successful: bool


class JudgeExperimentExecutionSubgraphState(
    JudgeExperimentExecutionSubgraphInputState,
    JudgeExperimentExecutionSubgraphHiddenState,
    JudgeExperimentExecutionSubgraphOutputState,
    ExecutionTimeState,
):
    pass


class JudgeExperimentExecutionSubgraph(BaseSubgraph):
    InputState = JudgeExperimentExecutionSubgraphInputState
    OutputState = JudgeExperimentExecutionSubgraphOutputState

    def __init__(
        self,
        llm_mapping: JudgeExperimentExecutionLLMMapping | None = None,
    ):
        self.llm_mapping = llm_mapping or JudgeExperimentExecutionLLMMapping()
        check_api_key(llm_api_key_check=True)

    @judge_experiment_execution_timed
    def _should_fix_code(
        self, state: JudgeExperimentExecutionSubgraphState
    ) -> dict[str, Any]:
        if not state.get("executed_flag"):
            return {
                "is_experiment_successful": False,
            }

        is_experiment_successful = should_fix_code(
            llm_name=self.llm_mapping.should_fix_code,
            output_text_data=state["new_method"].experimental_results.result,
            error_text_data=state["new_method"].experimental_results.error,
        )
        return {
            "is_experiment_successful": is_experiment_successful,
        }

    def build_graph(self) -> CompiledGraph:
        graph_builder = StateGraph(JudgeExperimentExecutionSubgraphState)
        graph_builder.add_node("should_fix_code", self._should_fix_code)

        graph_builder.add_edge(START, "should_fix_code")
        graph_builder.add_edge("should_fix_code", END)

        return graph_builder.compile()


def main():
    from airas.types.research_hypothesis import ExperimentalResults

    sample_experimental_results = ExperimentalResults(
        result="Training completed successfully. Final accuracy: 95.2%",
        error="",
    )

    sample_new_method = ResearchHypothesis(
        experimental_results=sample_experimental_results,
    )

    input_data = {
        "new_method": sample_new_method,
        "executed_flag": True,
    }

    result = JudgeExperimentExecutionSubgraph().run(input_data)
    print(f"result: {result}")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        logger.error(f"Error running JudgeExperimentExecutionSubgraph: {e}")
        raise
