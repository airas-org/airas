
import json
import logging
from typing import Any, Literal

from langgraph.graph import END, START, StateGraph
from langgraph.graph.graph import CompiledGraph
from typing_extensions import TypedDict

from airas.execution.executor_subgraph.input_data import executor_subgraph_input_data
from airas.execution.executor_subgraph.nodes.execute_github_actions_workflow import (
    execute_github_actions_workflow,
)
from airas.execution.executor_subgraph.nodes.retrieve_github_actions_artifacts import (
    retrieve_github_actions_artifacts,
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

    @executor_timed
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

    @executor_timed
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
    save_dir = "/workspaces/airas/data"
    input = executor_subgraph_input_data

    result = ExecutorSubgraph(
        save_dir=save_dir, 
    ).run(input)
    print(f"result: {json.dumps(result, indent=2)}")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        logger.error(f"Error running ExecutorSubgraph: {e}")
        raise
