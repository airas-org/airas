import logging
from typing import Any

from langgraph.graph import END, START, StateGraph
from pydantic import BaseModel
from typing_extensions import TypedDict

from airas.config.llm_config import DEFAULT_NODE_LLMS
from airas.core.base import BaseSubgraph
from airas.features.evaluate.judge_execution_subgraph.input_data import (
    judge_execution_subgraph_input_data,
)
from airas.features.evaluate.judge_execution_subgraph.nodes.judge_execution import (
    judge_execution,
)
from airas.services.api_client.llm_client.llm_facade_client import LLM_MODEL
from airas.types.github import GitHubRepositoryInfo
from airas.types.research_hypothesis import ResearchHypothesis
from airas.utils.check_api_key import check_api_key
from airas.utils.execution_timers import ExecutionTimeState, time_node
from airas.utils.logging_utils import setup_logging

setup_logging()
logger = logging.getLogger(__name__)


def judge_execution_timed(f):
    return time_node("judge_execution_subgraph")(f)  # noqa: E731


class JudgeExecutionLLMMapping(BaseModel):
    judge_execution: LLM_MODEL = DEFAULT_NODE_LLMS["judge_execution"]


class JudgeExecutionSubgraphInputState(TypedDict):
    new_method: ResearchHypothesis
    executed_flag: bool
    github_repository_info: GitHubRepositoryInfo


class JudgeExecutionSubgraphHiddenState(TypedDict): ...


class JudgeExecutionSubgraphOutputState(TypedDict):
    is_experiment_successful: bool


class JudgeExecutionSubgraphState(
    JudgeExecutionSubgraphInputState,
    JudgeExecutionSubgraphHiddenState,
    JudgeExecutionSubgraphOutputState,
    ExecutionTimeState,
):
    pass


class JudgeExecutionSubgraph(BaseSubgraph):
    InputState = JudgeExecutionSubgraphInputState
    OutputState = JudgeExecutionSubgraphOutputState

    def __init__(
        self,
        llm_mapping: dict[str, str] | JudgeExecutionLLMMapping | None = None,
    ):
        if llm_mapping is None:
            self.llm_mapping = JudgeExecutionLLMMapping()
        elif isinstance(llm_mapping, dict):
            self.llm_mapping = JudgeExecutionLLMMapping(**llm_mapping)
        elif isinstance(llm_mapping, JudgeExecutionLLMMapping):
            self.llm_mapping = llm_mapping
        else:
            raise TypeError(
                f"llm_mapping must be None, dict[str, str], or JudgeExecutionLLMMapping, "
                f"but got {type(llm_mapping)}"
            )
        check_api_key(llm_api_key_check=True)

    @judge_execution_timed
    def _judge_execution(self, state: JudgeExecutionSubgraphState) -> dict[str, Any]:
        if not state.get("executed_flag"):
            return {
                "is_experiment_successful": False,
            }

        is_experiment_successful = judge_execution(
            llm_name=self.llm_mapping.judge_execution,
            output_text_data=state["new_method"].experimental_results.result,
            error_text_data=state["new_method"].experimental_results.error,
        )
        return {
            "is_experiment_successful": is_experiment_successful,
        }

    def build_graph(self):
        graph_builder = StateGraph(JudgeExecutionSubgraphState)
        graph_builder.add_node("judge_execution", self._judge_execution)

        graph_builder.add_edge(START, "judge_execution")
        graph_builder.add_edge("judge_execution", END)

        return graph_builder.compile()


def main():
    input = judge_execution_subgraph_input_data
    result = JudgeExecutionSubgraph().run(input)

    print(f"result: {result}")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        logger.error(f"Error running JudgeExecutionSubgraph: {e}")
        raise
