import argparse
from logging import getLogger

from langgraph.graph import END, START, StateGraph
from langgraph.graph.graph import CompiledGraph
from typing_extensions import TypedDict

from airas.core.base import BaseSubgraph
from airas.features.github.nodes.create_branch import create_branch
from airas.features.github.nodes.find_commit_sha import find_commit_sha
from airas.utils.check_api_key import check_api_key
from airas.utils.execution_timers import ExecutionTimeState, time_node
from airas.utils.logging_utils import setup_logging

setup_logging()
logger = getLogger(__name__)

create_branch_timed = lambda f: time_node("create_branch_subgraph")(f)  # noqa: E731


class CreateBranchSubgraphInputState(TypedDict):
    github_repository: str
    branch_name: str


class CreateBranchSubgraphHiddenState(TypedDict):
    github_owner: str
    repository_name: str
    target_sha: str
    branch_created: bool


class CreateBranchSubgraphOutputState(TypedDict):
    branch_name: str


class CreateBranchSubgraphState(
    CreateBranchSubgraphInputState,
    CreateBranchSubgraphHiddenState,
    CreateBranchSubgraphOutputState,
    ExecutionTimeState,
): ...


class CreateBranchSubgraph(BaseSubgraph):
    InputState = CreateBranchSubgraphInputState
    OutputState = CreateBranchSubgraphOutputState

    def __init__(self, new_branch_name: str, up_to_subgraph: str):
        check_api_key(github_personal_access_token_check=True)
        self.new_branch_name = new_branch_name
        self.up_to_subgraph = up_to_subgraph

    def _init_state(self, state: CreateBranchSubgraphState) -> dict[str, str]:
        try:
            github_owner, repository_name = state["github_repository"].split("/", 1)
            return {
                "github_owner": github_owner,
                "repository_name": repository_name,
            }
        except ValueError:
            logger.error(
                f"Invalid github_repository format: {state['github_repository']}"
            )
            raise

    @create_branch_timed
    def _find_commit_sha(self, state: CreateBranchSubgraphState) -> dict[str, str]:
        target_sha = find_commit_sha(
            github_owner=state["github_owner"],
            repository_name=state["repository_name"],
            branch_name=state["branch_name"],
            subgraph_name=self.up_to_subgraph,
        )
        return {"target_sha": target_sha}

    @create_branch_timed
    def _create_branch(self, state: CreateBranchSubgraphState) -> dict[str, str]:
        branch_created = create_branch(
            github_owner=state["github_owner"],
            repository_name=state["repository_name"],
            branch_name=self.new_branch_name,
            sha=state["target_sha"],
        )
        if not branch_created:
            raise RuntimeError("Failed to create branch")
        return {"branch_name": self.new_branch_name}

    def build_graph(self) -> CompiledGraph:
        sg = StateGraph(CreateBranchSubgraphState)
        sg.add_node("init_state", self._init_state)
        sg.add_node("find_commit_sha", self._find_commit_sha)
        sg.add_node("create_branch", self._create_branch)

        sg.add_edge(START, "init_state")
        sg.add_edge("init_state", "find_commit_sha")
        sg.add_edge("find_commit_sha", "create_branch")
        sg.add_edge("create_branch", END)
        graph_builder = sg.compile()
        return graph_builder


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="CreateBranchSubgraph")
    parser.add_argument("github_repository", help="Your GitHub repository")
    parser.add_argument("branch_name", help="Your Branch name")
    parser.add_argument("new_branch_name", help="Name of new branch to create")
    parser.add_argument("up_to_subgraph", help="Subgraph name to keep up to")

    args = parser.parse_args()

    state = {
        "github_repository": args.github_repository,
        "branch_name": args.branch_name,
    }

    result = CreateBranchSubgraph(
        new_branch_name=args.new_branch_name,
        up_to_subgraph=args.up_to_subgraph,
    ).run(state)
    print(f"result: {result}")
