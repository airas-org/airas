import logging

from langgraph.graph import END, START, StateGraph
from typing_extensions import TypedDict

from airas.core.base import BaseSubgraph
from airas.features.create.create_code_with_devin_subgraph.input_data import (
    create_code_with_devin_subgraph_input_data,
)
from airas.features.create.create_code_with_devin_subgraph.nodes.push_code_with_devin import (
    push_code_with_devin,
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

push_code_timed = lambda f: time_node("push_code_subgraph")(f)  # noqa: E731


class CreateCodeWithDevinSubgraphInputState(TypedDict):
    new_method: ResearchHypothesis
    github_repository_info: GitHubRepositoryInfo


class CreateCodeWithDevinSubgraphHiddenState(TypedDict): ...


class CreateCodeWithDevinSubgraphOutputState(TypedDict):
    push_completion: bool
    devin_info: DevinInfo
    experiment_iteration: int


class CreateCodeWithDevinSubgraphState(
    CreateCodeWithDevinSubgraphInputState,
    CreateCodeWithDevinSubgraphHiddenState,
    CreateCodeWithDevinSubgraphOutputState,
    ExecutionTimeState,
):
    pass


class CreateCodeWithDevinSubgraph(BaseSubgraph):
    InputState = CreateCodeWithDevinSubgraphInputState
    OutputState = CreateCodeWithDevinSubgraphOutputState

    def __init__(
        self,
    ):
        check_api_key(
            devin_api_key_check=True,
            github_personal_access_token_check=True,
        )

    @push_code_timed
    def _init_state(self, state: CreateCodeWithDevinSubgraphState) -> dict[str, int]:
        logger.info("---PushCodeSubgraph---")
        return {"experiment_iteration": 1}

    @push_code_timed
    def _push_code_with_devin_node(
        self, state: CreateCodeWithDevinSubgraphState
    ) -> dict:
        devin_info = push_code_with_devin(
            github_repository_info=state["github_repository_info"],
            new_method=state["new_method"],
            experiment_iteration=state["experiment_iteration"],
        )
        return {
            "devin_info": devin_info,
        }

    @push_code_timed
    def _check_devin_completion_node(
        self, state: CreateCodeWithDevinSubgraphState
    ) -> dict[str, bool]:
        result = check_devin_completion(
            session_id=state["devin_info"].session_id,
        )
        if result is None:
            return {"push_completion": False}
        return {"push_completion": True}

    def build_graph(self):
        graph_builder = StateGraph(CreateCodeWithDevinSubgraphState)
        graph_builder.add_node("init_state", self._init_state)
        graph_builder.add_node(
            "push_code_with_devin_node", self._push_code_with_devin_node
        )
        graph_builder.add_node(
            "check_devin_completion_node", self._check_devin_completion_node
        )

        graph_builder.add_edge(START, "init_state")
        graph_builder.add_edge("init_state", "push_code_with_devin_node")
        graph_builder.add_edge(
            "push_code_with_devin_node", "check_devin_completion_node"
        )
        graph_builder.add_edge("check_devin_completion_node", END)
        return graph_builder.compile()


def main():
    input_data = create_code_with_devin_subgraph_input_data
    result = CreateCodeWithDevinSubgraph().run(input_data)
    print(f"result: {result}")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        logger.error(f"Error running CreateCodeWithDevinSubgraph: {e}")
        raise
