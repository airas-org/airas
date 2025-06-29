import argparse
import json
import logging
from typing import Any

from langgraph.graph import END, START, StateGraph
from langgraph.graph.graph import CompiledGraph
from typing_extensions import TypedDict

from airas.core.base import BaseSubgraph
from airas.features.github.nodes.github_download import github_download
from airas.utils.check_api_key import check_api_key
from airas.utils.execution_timers import ExecutionTimeState, time_node
from airas.utils.logging_utils import setup_logging

setup_logging()
logger = logging.getLogger(__name__)

gh_download_timed = lambda f: time_node("github_download_subgraph")(f)  # noqa: E731


class GithubDownloadInputState(TypedDict):
    github_repository: str
    branch_name: str


class GithubDownloadHiddenState(TypedDict):
    github_owner: str
    repository_name: str


class GithubDownloadOutputState(TypedDict):
    research_history: dict[str, Any]


class GithubDownloadSubgraphState(
    GithubDownloadInputState,
    GithubDownloadHiddenState,
    GithubDownloadOutputState,
    ExecutionTimeState,
):
    pass


class GithubDownloadSubgraph(BaseSubgraph):
    InputState = GithubDownloadInputState
    OutputState = GithubDownloadOutputState

    def __init__(self):
        check_api_key(
            github_personal_access_token_check=True,
        )
        self.research_file_path = ".research/research_history.json"

    def _init_state(self, state: GithubDownloadSubgraphState) -> dict[str, str]:
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

    @gh_download_timed
    def _github_download(self, state: GithubDownloadSubgraphState) -> dict[str, Any]:
        research_history = github_download(
            github_owner=state["github_owner"],
            repository_name=state["repository_name"],
            branch_name=state["branch_name"],
        )
        return {
            "research_history": research_history,
        }

    def build_graph(self) -> CompiledGraph:
        sg = StateGraph(GithubDownloadSubgraphState)
        sg.add_node("init_state", self._init_state)
        sg.add_node("github_download", self._github_download)

        sg.add_edge(START, "init_state")
        sg.add_edge("init_state", "github_download")
        sg.add_edge("github_download", END)
        return sg.compile()


if __name__ == "__main__":
    remote_dir = ".research"

    parser = argparse.ArgumentParser(description="GithubDownloadSubgraph")
    parser.add_argument("github_repository", help="Your GitHub repository")
    parser.add_argument(
        "branch_name", help="Your branch name in your GitHub repository"
    )

    args = parser.parse_args()

    state = {
        "github_repository": args.github_repository,
        "branch_name": args.branch_name,
    }

    result = GithubDownloadSubgraph().run(state)
    print(json.dumps(result, indent=2))
