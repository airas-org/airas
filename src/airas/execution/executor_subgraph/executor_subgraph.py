import argparse
import json
import logging
import os

from langgraph.graph import END, START, StateGraph
from langgraph.graph.graph import CompiledGraph
from typing import Literal
from typing_extensions import TypedDict


from airas.execution.executor_subgraph.nodes.execute_github_actions_workflow import (
    execute_github_actions_workflow,
)
from airas.execution.executor_subgraph.nodes.retrieve_github_actions_artifacts import (
    retrieve_github_actions_artifacts,
)
from airas.execution.executor_subgraph.input_data import executor_subgraph_input_data

from airas.utils.check_api_key import check_api_key
from airas.utils.execution_timers import ExecutionTimeState, time_node
from airas.utils.github_utils.graph_wrapper import create_wrapped_subgraph
from airas.utils.logging_utils import setup_logging

setup_logging()
logger = logging.getLogger(__name__)


class ExecutorSubgraphInputState(TypedDict):
    github_owner: str
    repository_name: str
    branch_name: str
    push_completion: Literal[True]


class ExecutorSubgraphHiddenState(TypedDict):
    workflow_run_id: int | None


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
    def __init__(
        self,
        save_dir: str,
    ):
        self.save_dir = save_dir
        check_api_key(
            github_personal_access_token_check=True,
        )

    @time_node("executor_subgraph", "_execute_github_actions_workflow_node")
    def _execute_github_actions_workflow_node(
        self, state: ExecutorSubgraphState
    ) -> dict:  
        if not state.get("push_completion", True):
            raise ValueError("ExecutorSubgraph was called without a successful code push (expected push_completion == True)")
        
        workflow_run_id = execute_github_actions_workflow(
            github_owner=state["github_owner"],
            repository_name=state["repository_name"],
            branch_name=state["branch_name"],
        )
        executed_flag = workflow_run_id is not None
        return {
            "workflow_run_id": workflow_run_id,
            "executed_flag": executed_flag,
        }

    @time_node("executor_subgraph", "_retrieve_github_actions_artifacts_node")
    def _retrieve_github_actions_artifacts_node(
        self, state: ExecutorSubgraphState
    ) -> dict:
        if state["workflow_run_id"] is None:
            logger.warning("Skipping artifact retrieval due to missing `workflow_run_id`.")
            return {
                "output_text_data": "",
                "error_text_data": "",
            }

        output_text_data, error_text_data = retrieve_github_actions_artifacts(
            github_owner=state["github_owner"],
            repository_name=state["repository_name"],
            workflow_run_id=state["workflow_run_id"],
            save_dir=self.save_dir,
        )
        return {
            "output_text_data": output_text_data,
            "error_text_data": error_text_data,
        }

    def build_graph(self) -> CompiledGraph:
        graph_builder = StateGraph(ExecutorSubgraphState)
        graph_builder.add_node("execute_github_actions_workflow_node", self._execute_github_actions_workflow_node)
        graph_builder.add_node("retrieve_github_actions_artifacts_node", self._retrieve_github_actions_artifacts_node)

        graph_builder.add_edge(START, "execute_github_actions_workflow_node")
        graph_builder.add_edge("execute_github_actions_workflow_node", "retrieve_github_actions_artifacts_node")
        graph_builder.add_edge("retrieve_github_actions_artifacts_node", END)
        return graph_builder.compile()


Executor = create_wrapped_subgraph(
    ExecutorSubgraph,
    ExecutorSubgraphInputState,
    ExecutorSubgraphOutputState,
)

def main():
    save_dir = "/workspaces/airas/data"

    parser = argparse.ArgumentParser(
        description="ExecutorSubgraph"
    )
    parser.add_argument("github_repository", help="Your GitHub repository")
    parser.add_argument(
        "branch_name", help="Your branch name in your GitHub repository"
    )
    args = parser.parse_args()

    ex = Executor(
        github_repository=args.github_repository,
        branch_name=args.branch_name,
        save_dir=save_dir, 
    )
    result = ex.run()
    print(f"result: {json.dumps(result, indent=2)}")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        logger.error(f"Error running ExecutorSubgraph: {e}")
        raise
