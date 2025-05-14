import argparse
import json
import logging
import os

from langgraph.graph import END, START, StateGraph
from langgraph.graph.graph import CompiledGraph
from typing_extensions import TypedDict

from airas.execution.executor_subgraph.nodes.check_devin_completion import (
    check_devin_completion,
)
from airas.execution.executor_subgraph.nodes.execute_github_actions_workflow import (
    execute_github_actions_workflow,
)
from airas.execution.executor_subgraph.nodes.fix_code_with_devin import (
    fix_code_with_devin,
)
from airas.execution.executor_subgraph.nodes.generate_code_with_devin import (
    generate_code_with_devin,
)
from airas.execution.executor_subgraph.nodes.llm_decide import llm_decide
from airas.execution.executor_subgraph.nodes.retrieve_github_actions_artifacts import (
    retrieve_github_actions_artifacts,
)
from airas.execution.executor_subgraph.prompt.llm_decide import (
    llm_decide_prompt,
)
from airas.utils.check_api_key import check_api_key
from airas.utils.execution_timers import ExecutionTimeState, time_node
from airas.utils.github_utils.graph_wrapper import create_wrapped_subgraph
from airas.utils.logging_utils import setup_logging

setup_logging()
logger = logging.getLogger(__name__)


class ExecutorSubgraphInputState(TypedDict):
    new_method: str
    experiment_code: str
    github_owner: str
    repository_name: str
    branch_name: str


class ExecutorSubgraphHiddenState(TypedDict):
    experiment_session_id: str
    devin_completion: bool
    fix_iteration_count: int
    error_text_data: str
    judgment_result: bool
    workflow_run_id: int


class ExecutorSubgraphOutputState(TypedDict):
    experiment_devin_url: str
    branch_name: str
    output_text_data: str


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
        max_code_fix_iteration: int = 3,
    ):
        self.save_dir = save_dir
        self.max_code_fix_iteration = max_code_fix_iteration
        self.headers = {
            "Authorization": f"Bearer {os.getenv('DEVIN_API_KEY')}",
            "Content-Type": "application/json",
        }
        check_api_key(
            llm_api_key_check=True,
            devin_api_key_check=True,
            github_personal_access_token_check=True,
        )

    @time_node("executor_subgraph", "_generate_code_with_devin_node")
    def _generate_code_with_devin_node(self, state: ExecutorSubgraphState) -> dict:
        logger.info("---ExecutorSubgraph---")
        branch_name=state["branch_name"]
        experiment_session_id, experiment_devin_url = generate_code_with_devin(
            headers=self.headers,
            github_owner=state["github_owner"],
            repository_name=state["repository_name"],
            branch_name=branch_name,
            new_method=state["new_method"],
            experiment_code=state["experiment_code"],
        )

        return {
            "fix_iteration_count": 0,
            "experiment_session_id": experiment_session_id,
            "branch_name": branch_name,
            "experiment_devin_url": experiment_devin_url,
        }

    @time_node("executor_subgraph", "_check_devin_completion_node")
    def _check_devin_completion_node(self, state: ExecutorSubgraphState) -> dict:
        result = check_devin_completion(
            headers=self.headers,
            session_id=state["experiment_session_id"],
        )
        if result is None:
            return {"devin_completion": False}
        return {"devin_completion": True}

    @time_node("executor_subgraph", "_execute_github_actions_workflow_node")
    def _execute_github_actions_workflow_node(
        self, state: ExecutorSubgraphState
    ) -> dict:
        workflow_run_id = execute_github_actions_workflow(
            github_owner=state["github_owner"],
            repository_name=state["repository_name"],
            branch_name=state["branch_name"],
        )
        return {
            "workflow_run_id": workflow_run_id,
        }

    @time_node("executor_subgraph", "_retrieve_github_actions_artifacts_node")
    def _retrieve_github_actions_artifacts_node(
        self, state: ExecutorSubgraphState
    ) -> dict:
        output_text_data, error_text_data = retrieve_github_actions_artifacts(
            github_owner=state["github_owner"],
            repository_name=state["repository_name"],
            workflow_run_id=state["workflow_run_id"],
            save_dir=self.save_dir,
            fix_iteration_count=state["fix_iteration_count"],
        )
        return {
            "output_text_data": output_text_data,
            "error_text_data": error_text_data,
        }

    @time_node("executor_subgraph", "_llm_decide_node")
    def _llm_decide_node(self, state: ExecutorSubgraphState) -> dict:
        judgment_result = llm_decide(
            llm_name="o3-mini-2025-01-31",
            output_text_data=state["output_text_data"],
            error_text_data=state["error_text_data"],
            prompt_template=llm_decide_prompt, 
        )
        return {
            "judgment_result": judgment_result,
        }

    @time_node("executor_subgraph", "_fix_code_with_devin_node")
    def _fix_code_with_devin_node(self, state: ExecutorSubgraphState) -> dict:
        fix_iteration_count = fix_code_with_devin(
            headers=self.headers,
            session_id=state["experiment_session_id"],
            output_text_data=state["output_text_data"],
            error_text_data=state["error_text_data"],
            fix_iteration_count=state["fix_iteration_count"],
        )
        return {
            "fix_iteration_count": fix_iteration_count,
        }

    def iteration_function(self, state: ExecutorSubgraphState):
        if state["judgment_result"] is True:
            return "finish"
        else:
            if state["fix_iteration_count"] < self.max_code_fix_iteration:
                return "correction"
            else:
                return "finish"

    def build_graph(self) -> CompiledGraph:
        graph_builder = StateGraph(ExecutorSubgraphState)
        # make nodes
        graph_builder.add_node(
            "generate_code_with_devin_node", self._generate_code_with_devin_node
        )
        graph_builder.add_node(
            "check_devin_completion_node", self._check_devin_completion_node
        )
        graph_builder.add_node(
            "execute_github_actions_workflow_node",
            self._execute_github_actions_workflow_node,
        )
        graph_builder.add_node(
            "retrieve_github_actions_artifacts_node",
            self._retrieve_github_actions_artifacts_node,
        )
        graph_builder.add_node("llm_decide_node", self._llm_decide_node)
        graph_builder.add_node(
            "fix_code_with_devin_node", self._fix_code_with_devin_node
        )

        # make edges
        graph_builder.add_edge(START, "generate_code_with_devin_node")
        graph_builder.add_edge(
            "generate_code_with_devin_node", "check_devin_completion_node"
        )
        graph_builder.add_conditional_edges(
            "check_devin_completion_node",
            path=lambda state: state["devin_completion"],
            path_map={
                True: "execute_github_actions_workflow_node",
                False: END,
            },
        )
        graph_builder.add_edge(
            "execute_github_actions_workflow_node",
            "retrieve_github_actions_artifacts_node",
        )
        graph_builder.add_edge(
            "retrieve_github_actions_artifacts_node", "llm_decide_node"
        )
        graph_builder.add_conditional_edges(
            "llm_decide_node",
            self.iteration_function,
            {
                "correction": "fix_code_with_devin_node",
                "finish": END,
            },
        )
        graph_builder.add_edge(
            "fix_code_with_devin_node", "check_devin_completion_node"
        )
        graph_builder.add_edge(
            "check_devin_completion_node", "execute_github_actions_workflow_node"
        )
        return graph_builder.compile()


Executor = create_wrapped_subgraph(
    ExecutorSubgraph,
    ExecutorSubgraphInputState,
    ExecutorSubgraphOutputState,
)

def main():
    max_code_fix_iteration = 1
    save_dir = "/workspaces/airas/data"

    parser = argparse.ArgumentParser(
        description="Execute ExecutorSubgraph"
    )
    parser.add_argument("github_repository", help="Your GitHub repository")
    parser.add_argument(
        "branch_name", help="Your branch name in your GitHub repository"
    )
    args = parser.parse_args()

    ex = Executor(
        github_repository=args.github_repository,
        branch_name=args.branch_name,
        max_code_fix_iteration=max_code_fix_iteration, 
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
