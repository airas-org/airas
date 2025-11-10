import argparse
import asyncio
import logging
from typing import Any

from langgraph.graph import END, START, StateGraph
from langgraph.graph.graph import CompiledGraph
from typing_extensions import TypedDict

from airas.core.base import BaseSubgraph
from airas.features.github.nodes.github_download import github_download
from airas.services.api_client.github_client import GithubClient
from airas.types.github import GitHubRepositoryInfo
from airas.types.research_history import ResearchHistory
from airas.utils.check_api_key import check_api_key
from airas.utils.execution_timers import ExecutionTimeState, time_node
from airas.utils.logging_utils import setup_logging

setup_logging()
logger = logging.getLogger(__name__)

gh_download_timed = lambda f: time_node("github_download_subgraph")(f)  # noqa: E731


class GithubDownloadInputState(TypedDict):
    github_repository_info: GitHubRepositoryInfo


class GithubDownloadHiddenState(TypedDict):
    pass


class GithubDownloadOutputState(TypedDict):
    research_history: ResearchHistory


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

    def __init__(self, github_client: GithubClient):
        check_api_key(
            github_personal_access_token_check=True,
        )
        self.research_file_path = ".research/research_history.json"
        self.github_client = github_client

    @gh_download_timed
    def _github_download(
        self, state: GithubDownloadSubgraphState
    ) -> dict[str, ResearchHistory]:
        research_history = github_download(
            github_repository_info=state["github_repository_info"],
            github_client=self.github_client,
        )
        return {
            "research_history": research_history,
        }

    def build_graph(self) -> CompiledGraph:
        sg = StateGraph(GithubDownloadSubgraphState)
        sg.add_node("github_download", self._github_download)

        sg.add_edge(START, "github_download")
        sg.add_edge("github_download", END)
        return sg.compile()

    def run(self, state: dict[str, Any], config: dict | None = None) -> dict[str, Any]:
        return asyncio.run(self.arun(state, config=config))

    async def arun(
        self, state: dict[str, Any], config: dict | None = None
    ) -> dict[str, Any]:
        input_state_keys = self.InputState.__annotations__.keys()
        input_state = {k: state[k] for k in input_state_keys if k in state}

        config = config or {"recursion_limit": 200}
        result = await self.build_graph().ainvoke(input_state, config=config)

        research_history: ResearchHistory = result.get("research_history", {})
        flat_fields = {
            field: getattr(research_history, field)
            for field in research_history.model_fields
            if getattr(research_history, field) is not None
        }
        return {**state, **flat_fields}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="GithubDownloadSubgraph")
    parser.add_argument("github_repository", help="Your GitHub repository")
    parser.add_argument(
        "branch_name", help="Your branch name in your GitHub repository"
    )

    args = parser.parse_args()

    github_repository_info = GitHubRepositoryInfo(
        github_owner=args.github_repository.split("/")[0],
        repository_name=args.github_repository.split("/")[1],
        branch_name=args.branch_name,
    )
    state = {
        "github_repository_info": github_repository_info,
    }
    state = GithubDownloadSubgraph().run(state)
    print(f"state {state.keys()}")
