
import json
import logging
from typing import Literal
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
    github_owner: str
    repository_name: str
    branch_name: str
    gpu_enabled: bool
    experiment_iteration: int
    push_completion: Literal[True]


class ExecutorSubgraphHiddenState(TypedDict):
    pass


class ExecutorSubgraphOutputState(TypedDict):
    output_text_data: str
    error_text_data: str
    executed_flag: bool


class ExecutorSubgraphState(
    ExecutorSubgraphInputState,
    ExecutorSubgraphHiddenState,
    ExecutorSubgraphOutputState,
    ExecutionTimeState,
):
    pass


class ExecutorSubgraph:
    def __init__(self):
        check_api_key(
            github_personal_access_token_check=True,
        )

    @executor_timed
    def _execute_github_actions_workflow_node(
        self, state: ExecutorSubgraphState
    ) -> dict:  
        if not state.get("push_completion", True):
            raise ValueError("ExecutorSubgraph was called without a successful code push (expected push_completion == True)")
        
        executed_flag, experiment_iteration = execute_github_actions_workflow(
            github_owner=state["github_owner"],
            repository_name=state["repository_name"],
            branch_name=state["branch_name"],
            experiment_iteration=state["experiment_iteration"],
            gpu_enabled=state["gpu_enabled"],
        )
        return {
            "executed_flag": executed_flag,
            "experiment_iteration": experiment_iteration,
        }

    @executor_timed
    def _retrieve_github_actions_artifacts_node(
        self, state: ExecutorSubgraphState
    ) -> dict:
        output_text_data, error_text_data = retrieve_github_actions_results(
            github_owner=state["github_owner"],
            repository_name=state["repository_name"],
            branch_name=state["branch_name"],
            experiment_iteration=state["experiment_iteration"],
        )
        return {
            "output_text_data": output_text_data,
            "error_text_data": error_text_data,
            # NOTE: We increment the experiment_iteration here to reflect the next iteration
            "experiment_iteration": state["experiment_iteration"] + 1,
        }

    def build_graph(self) -> CompiledGraph:
        graph_builder = StateGraph(ExecutorSubgraphState)
        graph_builder.add_node("execute_github_actions_workflow_node", self._execute_github_actions_workflow_node)
        graph_builder.add_node("retrieve_github_actions_artifacts_node", self._retrieve_github_actions_artifacts_node)

        graph_builder.add_edge(START, "execute_github_actions_workflow_node")
        graph_builder.add_edge("execute_github_actions_workflow_node", "retrieve_github_actions_artifacts_node")
        graph_builder.add_edge("retrieve_github_actions_artifacts_node", END)
        return graph_builder.compile()

    def run(
        self, 
        input: ExecutorSubgraphInputState, 
        config: dict | None = None
    ) -> dict:
        graph = self.build_graph()
        result = graph.invoke(input, config=config or {})

        #output_keys = ExecutorSubgraphOutputState.__annotations__.keys()
        #output = {k: result[k] for k in output_keys if k in result}
        return result

def main():
    parser = argparse.ArgumentParser(
        description="ExecutorSubgraph"
    )
    parser.add_argument("github_owner", help="Your GitHub owner/organization name")
    parser.add_argument("repository_name", help="Your GitHub repository")
    parser.add_argument(
        "branch_name", help="Your branch name in your GitHub repository"
    )
    args = parser.parse_args()

    state = {
        "github_owner": args.github_owner,
        "repository_name": args.repository_name,
        "branch_name": args.branch_name,
        "gpu_enabled": False,
        "experiment_iteration": 1,
        "push_completion": True,  # Set to True to indicate a successful code push
    }
    result = ExecutorSubgraph().run(
        input=state
    )
    print(f"result: {json.dumps(result, indent=2, ensure_ascii=False)}")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        logger.error(f"Error running ExecutorSubgraph: {e}")
        raise
