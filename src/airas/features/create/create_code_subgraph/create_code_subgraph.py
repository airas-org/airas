import logging
from typing import cast

from langgraph.graph import END, START, StateGraph
from langgraph.graph.graph import CompiledGraph
from typing_extensions import TypedDict

from airas.core.base import BaseSubgraph
from airas.features.create.create_code_subgraph.nodes.push_code_with_devin import (
    push_code_with_devin,
)
from airas.features.create.nodes.check_devin_completion import (
    check_devin_completion,
)
from airas.types.devin import DevinInfo
from airas.types.github import GitHubRepository
from airas.types.method import MLMethodData
from airas.utils.check_api_key import check_api_key
from airas.utils.execution_timers import ExecutionTimeState, time_node
from airas.utils.logging_utils import setup_logging

setup_logging()
logger = logging.getLogger(__name__)

push_code_timed = lambda f: time_node("push_code_subgraph")(f)  # noqa: E731


class CreateCodeSubgraphInputState(TypedDict):
    new_method: MLMethodData
    # experiment_code: str
    experiment_repository: GitHubRepository
    # github_repository: str
    # branch_name: str


class CreateCodeSubgraphHiddenState(TypedDict): ...


class CreateCodeSubgraphOutputState(TypedDict):
    push_completion: bool
    experiment_session_id: str
    experiment_devin_url: str
    experiment_iteration: int


class CreateCodeSubgraphState(
    # CreateCodeSubgraphInputState,
    # CreateCodeSubgraphHiddenState,
    # CreateCodeSubgraphOutputState,
    ExecutionTimeState,
):
    new_method: MLMethodData
    experiment_repository: GitHubRepository
    devin_info: DevinInfo


class CreateCodeSubgraph(BaseSubgraph):
    InputState = CreateCodeSubgraphInputState
    OutputState = CreateCodeSubgraphOutputState

    def __init__(
        self,
    ):
        check_api_key(
            devin_api_key_check=True,
            github_personal_access_token_check=True,
        )

    @push_code_timed
    def _init_state(self, state: CreateCodeSubgraphState) -> dict:
        new_method = state["new_method"]
        new_method.experiment_meta_info.iteration = 1
        return {"new_method": new_method}

    @push_code_timed
    def _push_code_with_devin_node(self, state: CreateCodeSubgraphState) -> dict:
        experiment_repository = state["experiment_repository"]
        new_method = state["new_method"]
        experiment_session_id, experiment_devin_url = push_code_with_devin(
            github_owner=experiment_repository.github_owner,
            repository_name=experiment_repository.repository_name,
            branch_name=experiment_repository.branch_name,
            new_method=new_method.method,
            experiment_code=cast(str, new_method.experiment_code),
            experiment_iteration=cast(int, new_method.experiment_meta_info.iteration),
        )
        devin_info = DevinInfo(
            session_id=experiment_session_id,
            devin_url=experiment_devin_url,
        )
        return {
            "devin_info": devin_info,
        }

    @push_code_timed
    def _check_devin_completion_node(self, state: CreateCodeSubgraphState) -> dict:
        devin_info = state["devin_info"]
        new_method = state["new_method"]
        result = check_devin_completion(
            session_id=devin_info.session_id,
        )
        if result is None:
            # TODO:この分岐を確認する
            new_method.experiment_meta_info.push_completion = False
            return {"new_method": new_method}
        new_method.experiment_meta_info.push_completion = True
        return {"new_method": new_method}

    def build_graph(self) -> CompiledGraph:
        graph_builder = StateGraph(CreateCodeSubgraphState)
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


# def main():
#     input = CreateCodeSubgraphInputState(
#         new_method="example_method",
#         experiment_code="print('Hello, world!')",
#         github_repository="auto-res2/test-tanaka-v11",
#         branch_name="develop",
#     )
#     result = CreateCodeSubgraph().run(input)
#     print(f"result: {json.dumps(result, indent=2)}")


# if __name__ == "__main__":
#     try:
#         main()
#     except Exception as e:
#         logger.error(f"Error running PushCodeSubgraph: {e}")
#         raise
