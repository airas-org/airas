
import json
import logging
from typing import Literal, Any
import argparse

from langgraph.graph import END, START, StateGraph
from langgraph.graph.graph import CompiledGraph
from typing_extensions import TypedDict

#from airas.execution.executor_subgraph.input_data import executor_subgraph_input_data
from airas.execution.executor_subgraph.nodes.execute_github_actions_workflow import (
    execute_github_actions_workflow,
)
from airas.execution.executor_subgraph.nodes.retrieve_github_actions_results import (
    retrieve_github_actions_results,
)

from airas.utils.check_api_key import check_api_key
from airas.utils.execution_timers import ExecutionTimeState, time_node
from airas.utils.logging_utils import setup_logging

setup_logging()
logger = logging.getLogger(__name__)

executor_timed = lambda f: time_node("executor_subgraph")(f)  # noqa: E731


class ExecutorSubgraphInputState(TypedDict):
    github_repository: str
    branch_name: str
    experiment_iteration: int
    push_completion: Literal[True]


class ExecutorSubgraphHiddenState(TypedDict):
    pass


class ExecutorSubgraphOutputState(TypedDict):
    output_text_data: str
    error_text_data: str
    image_file_name_list: list[str]
    executed_flag: bool


class ExecutorSubgraphState(
    ExecutorSubgraphInputState,
    ExecutorSubgraphHiddenState,
    ExecutorSubgraphOutputState,
    ExecutionTimeState,
):
    pass


class ExecutorSubgraph:
    def __init__(
        self, 
        gpu_enabled: bool = False
    ):
        check_api_key(
            github_personal_access_token_check=True,
        )
        self.gpu_enabled = gpu_enabled

    @executor_timed
    def _execute_github_actions_workflow_node(
        self, state: ExecutorSubgraphState
    ) -> dict:  
        if not state.get("push_completion", True):
            raise ValueError("ExecutorSubgraph was called without a successful code push (expected push_completion == True)")
        
        executed_flag = execute_github_actions_workflow(
            github_repository=state["github_repository"],
            branch_name=state["branch_name"],
            experiment_iteration=state["experiment_iteration"],
            gpu_enabled=self.gpu_enabled,
        )
        return {
            "executed_flag": executed_flag
        }

    @executor_timed
    def _retrieve_github_actions_results(
        self, state: ExecutorSubgraphState
    ) -> dict:
        output_text_data, error_text_data, image_file_name_list = retrieve_github_actions_results(
            github_repository=state["github_repository"],
            branch_name=state["branch_name"],
            experiment_iteration=state["experiment_iteration"],
        )
        return {
            "output_text_data": output_text_data,
            "error_text_data": error_text_data,
            "image_file_name_list": image_file_name_list,
            # NOTE: We increment the experiment_iteration here to reflect the next iteration
            "experiment_iteration": state["experiment_iteration"] + 1,
        }

    def build_graph(self) -> CompiledGraph:
        graph_builder = StateGraph(ExecutorSubgraphState)
        graph_builder.add_node("execute_github_actions_workflow_node", self._execute_github_actions_workflow_node)
        graph_builder.add_node("retrieve_github_actions_artifacts_node", self._retrieve_github_actions_results)

        graph_builder.add_edge(START, "execute_github_actions_workflow_node")
        graph_builder.add_edge("execute_github_actions_workflow_node", "retrieve_github_actions_artifacts_node")
        graph_builder.add_edge("retrieve_github_actions_artifacts_node", END)
        return graph_builder.compile()

    def run(
        self, 
        state: dict[str, Any], 
        config: dict | None = None
    ) -> dict[str, Any]:
        input_state_keys = ExecutorSubgraphInputState.__annotations__.keys()
        output_state_keys = ExecutorSubgraphOutputState.__annotations__.keys()

        input_state = {k: state[k] for k in input_state_keys if k in state}
        result = self.build_graph().invoke(input_state, config=config or {})
        output_state = {k: result[k] for k in output_state_keys if k in result}

        cleaned_state = {k: v for k, v in state.items() if k != "subgraph_name"}

        return {
            "subgraph_name": self.__class__.__name__,
            **cleaned_state,
            **output_state, 
        }


def main():
    parser = argparse.ArgumentParser(
        description="ExecutorSubgraph"
    )
    parser.add_argument("github_repository", help="Your GitHub repository")
    parser.add_argument(
        "branch_name", help="Your branch name in your GitHub repository"
    )
    args = parser.parse_args()

    state = {
        "github_repository": args.github_repository, 
        "branch_name": args.branch_name,
        "experiment_iteration": 1,
        "push_completion": True,  # Set to True to indicate a successful code push
    }
    result = ExecutorSubgraph().run(state)
    print(f"result: {json.dumps(result, indent=2, ensure_ascii=False)}")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        logger.error(f"Error running ExecutorSubgraph: {e}")
        raise
