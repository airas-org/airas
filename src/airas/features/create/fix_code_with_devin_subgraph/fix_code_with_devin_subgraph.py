import logging
from typing import cast

from langgraph.graph import END, START, StateGraph
from langgraph.graph.graph import CompiledGraph
from pydantic import BaseModel
from typing_extensions import TypedDict

from airas.config.runner_type_info import RunnerType
from airas.core.base import BaseSubgraph
from airas.features.create.fix_code_with_devin_subgraph.nodes.fix_code_with_devin import (
    fix_code_with_devin,
)
from airas.features.create.fix_code_with_devin_subgraph.nodes.initial_session_fix_code_with_devin import (
    initial_session_fix_code_with_devin,
)
from airas.features.create.nodes.check_devin_completion import (
    check_devin_completion,
)
from airas.types.devin import DevinInfo
from airas.types.github import GitHubRepositoryInfo
from airas.types.research_hypothesis import ResearchHypothesis
from airas.utils.check_api_key import check_api_key
from airas.utils.execution_timers import ExecutionTimeState, time_node
from airas.utils.logging_utils import setup_logging

setup_logging()
logger = logging.getLogger(__name__)

fix_code_timed = lambda f: time_node("fix_code_subgraph")(f)  # noqa: E731


class FixCodeWithDevinLLMMapping(BaseModel): ...


class FixCodeWithDevinSubgraphInputState(TypedDict):
    devin_info: DevinInfo
    new_method: ResearchHypothesis
    executed_flag: bool  # This should be True if the GitHub Actions workflow was executed successfully
    experiment_iteration: int
    github_repository_info: GitHubRepositoryInfo


class FixCodeWithDevinSubgraphHiddenState(TypedDict):
    push_completion: bool


class FixCodeWithDevinSubgraphOutputState(TypedDict):
    executed_flag: bool
    experiment_iteration: int
    is_code_pushed_to_github: bool
    error_list: list[str]
    devin_info: DevinInfo


class FixCodeWithDevinSubgraphState(
    FixCodeWithDevinSubgraphInputState,
    FixCodeWithDevinSubgraphHiddenState,
    FixCodeWithDevinSubgraphOutputState,
    ExecutionTimeState,
):
    pass


class FixCodeWithDevinSubgraph(BaseSubgraph):
    InputState = FixCodeWithDevinSubgraphInputState
    OutputState = FixCodeWithDevinSubgraphOutputState

    def __init__(self, runner_type: RunnerType = "ubuntu-latest"):
        self.runner_type = runner_type
        check_api_key(
            devin_api_key_check=True,
            github_personal_access_token_check=True,
        )

    def _initialize(
        self, state: FixCodeWithDevinSubgraphState
    ) -> dict[str, int | list[str] | dict[str, dict[str, list[str]]]]:
        # NOTE: We increment the experiment_iteration here to reflect the next iteration
        if state["error_list"]:
            error_list = state["error_list"]
        else:
            error_list = []
        return {
            "experiment_iteration": state["experiment_iteration"] + 1,
            "error_list": error_list,
        }

    # Devinのセッションがあるか確認
    def _check_devin_session(self, state: FixCodeWithDevinSubgraphState):
        if state["devin_info"]:
            return "pass"
        else:
            return "create_devin_session"

    @fix_code_timed
    def _initial_session_fix_code_with_devin(
        self, state: FixCodeWithDevinSubgraphState
    ) -> dict:
        devin_info = initial_session_fix_code_with_devin(
            github_repository_info=state["github_repository_info"],
            new_method=state["new_method"],
            experiment_iteration=state["experiment_iteration"],
            runner_type=cast(RunnerType, self.runner_type),
            error_list=state["error_list"],
        )
        return {
            "devin_info": devin_info,
        }

    @fix_code_timed
    def _fix_code_with_devin(self, state: FixCodeWithDevinSubgraphState) -> dict:
        fix_code_with_devin(
            new_method=state["new_method"],
            experiment_iteration=state["experiment_iteration"],
            runner_type=cast(RunnerType, self.runner_type),
            devin_info=state["devin_info"],
            error_list=state["error_list"],
        )
        return {"executed_flag": False}

    def _check_devin_completion_node(
        self, state: FixCodeWithDevinSubgraphState
    ) -> dict[str, bool]:
        result = check_devin_completion(
            session_id=state["devin_info"].session_id,
        )
        if result is None:
            return {"push_completion": False}
        return {"push_completion": True}

    def build_graph(self) -> CompiledGraph:
        graph_builder = StateGraph(FixCodeWithDevinSubgraphState)
        graph_builder.add_node("initialize", self._initialize)
        graph_builder.add_node(
            "initial_session_fix_code_with_devin",
            self._initial_session_fix_code_with_devin,
        )
        graph_builder.add_node("fix_code_with_devin_node", self._fix_code_with_devin)
        graph_builder.add_node(
            "check_devin_completion_node", self._check_devin_completion_node
        )

        graph_builder.add_edge(START, "initialize")
        graph_builder.add_conditional_edges(
            "initialize",
            self._check_devin_session,
            {
                "pass": "fix_code_with_devin_node",
                "create_devin_session": "initial_session_fix_code_with_devin",
            },
        )
        graph_builder.add_edge(
            "initial_session_fix_code_with_devin", "check_devin_completion_node"
        )
        graph_builder.add_edge(
            "fix_code_with_devin_node", "check_devin_completion_node"
        )
        graph_builder.add_edge("check_devin_completion_node", END)
        return graph_builder.compile()


# def main():
#     # input = {}
#     # result = FixCodeSubgraph().run(input)
#     print(f"result: {json.dumps(result, indent=2)}")

# if __name__ == "__main__":
#     try:
#         main()
#     except Exception as e:
#         logger.error(f"Error running FixCodeSubgraph: {e}")
#         raise
