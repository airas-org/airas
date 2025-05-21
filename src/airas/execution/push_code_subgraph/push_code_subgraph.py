import argparse
import json
import logging
import os

from langgraph.graph import END, START, StateGraph
from langgraph.graph.graph import CompiledGraph
from typing_extensions import TypedDict

from airas.execution.push_code_subgraph.nodes.check_devin_completion import (
    check_devin_completion,
)
from airas.execution.push_code_subgraph.nodes.push_code_with_devin import (
    push_code_with_devin,
)
from airas.execution.push_code_subgraph.input_data import push_code_subgraph_input_data
from airas.utils.github_utils.graph_wrapper import create_wrapped_subgraph
from airas.utils.check_api_key import check_api_key
from airas.utils.execution_timers import ExecutionTimeState, time_node
from airas.utils.logging_utils import setup_logging

setup_logging()
logger = logging.getLogger(__name__)


class PushCodeSubgraphInputState(TypedDict):
    new_method: str
    experiment_code: str
    github_owner: str
    repository_name: str
    branch_name: str


class PushCodeSubgraphHiddenState(TypedDict):
    ...
    

class PushCodeSubgraphOutputState(TypedDict):
    push_completion: bool
    experiment_session_id: str
    experiment_devin_url: str


class PushCodeSubgraphState(
    PushCodeSubgraphInputState,
    PushCodeSubgraphHiddenState,
    PushCodeSubgraphOutputState,
    ExecutionTimeState,
):
    pass


class PushCodeSubgraph:
    def __init__(
        self,
    ):
        self.headers = {
            "Authorization": f"Bearer {os.getenv('DEVIN_API_KEY')}",
            "Content-Type": "application/json",
        }
        check_api_key(
            devin_api_key_check=True,
            github_personal_access_token_check=True,
        )

    @time_node("push_code_subgraph", "_push_code_with_devin_node")
    def _push_code_with_devin_node(self, state: PushCodeSubgraphState) -> dict[str, str]:
        logger.info("---PushCodeSubgraph---")
        branch_name=state["branch_name"]
        experiment_session_id, experiment_devin_url = push_code_with_devin(
            headers=self.headers,
            github_owner=state["github_owner"],
            repository_name=state["repository_name"],
            branch_name=branch_name,
            new_method=state["new_method"],
            experiment_code=state["experiment_code"],
        )

        return {
            "experiment_session_id": experiment_session_id,
            "branch_name": branch_name,
            "experiment_devin_url": experiment_devin_url,
        }

    @time_node("push_code_subgraph", "_check_devin_completion_node")
    def _check_devin_completion_node(self, state: PushCodeSubgraphState) -> dict[str, bool]:
        result = check_devin_completion(
            headers=self.headers,
            session_id=state["experiment_session_id"],
        )
        if result is None:
            return {"push_completion": False}
        return {"push_completion": True}


    def build_graph(self) -> CompiledGraph:
        graph_builder = StateGraph(PushCodeSubgraphState)
        graph_builder.add_node("push_code_with_devin_node", self._push_code_with_devin_node)
        graph_builder.add_node("check_devin_completion_node", self._check_devin_completion_node)

        graph_builder.add_edge(START, "push_code_with_devin_node")
        graph_builder.add_edge("push_code_with_devin_node", "check_devin_completion_node")
        graph_builder.add_edge("check_devin_completion_node", END)
        return graph_builder.compile()


PushCode = create_wrapped_subgraph(
    PushCodeSubgraph,
    PushCodeSubgraphInputState,
    PushCodeSubgraphOutputState,
)

def main():
    parser = argparse.ArgumentParser(
        description="PushCodeSubgraph"
    )
    parser.add_argument("github_repository", help="Your GitHub repository")
    parser.add_argument(
        "branch_name", help="Your branch name in your GitHub repository"
    )
    args = parser.parse_args()

    pc= PushCode(
        github_repository=args.github_repository,
        branch_name=args.branch_name,
    )
    result = pc.run()
    print(f"result: {json.dumps(result, indent=2)}")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        logger.error(f"Error running PushCodeSubgraph: {e}")
        raise
