import argparse
import asyncio
import logging
from datetime import datetime
from typing import Any

from langgraph.graph import END, START, StateGraph
from typing_extensions import TypedDict

from airas.core.base import BaseSubgraph
from airas.features.github.nodes.github_download import github_download
from airas.features.github.nodes.github_upload import github_upload
from airas.features.github.nodes.merge_history import merge_history
from airas.services.api_client.github_client import GithubClient
from airas.types.github import GitHubRepositoryInfo
from airas.types.research_history import ResearchHistory
from airas.utils.check_api_key import check_api_key
from airas.utils.execution_timers import ExecutionTimeState, time_node
from airas.utils.logging_utils import setup_logging

setup_logging()
logger = logging.getLogger(__name__)
gh_upload_timed = lambda f: time_node("github_upload_subgraph")(f)  # noqa: E731


class GithubUploadInputState(TypedDict):
    github_repository_info: GitHubRepositoryInfo
    subgraph_name: str


class GithubUploadHiddenState(TypedDict):
    research_history: ResearchHistory
    cumulative_data: ResearchHistory
    is_github_upload_success: bool


class GithubUploadOutputState(TypedDict): ...


class GithubUploadSubgraphState(
    GithubUploadInputState,
    GithubUploadHiddenState,
    GithubUploadOutputState,
    ExecutionTimeState,
):
    pass


class GithubUploadSubgraph(BaseSubgraph):
    InputState = GithubUploadInputState
    OutputState = GithubUploadOutputState

    def __init__(self, github_client: GithubClient):
        check_api_key(
            github_personal_access_token_check=True,
        )
        self.research_file_path = ".research/research_history.json"
        self.github_client = github_client

    @gh_upload_timed
    def _github_download_node(
        self, state: GithubUploadSubgraphState
    ) -> dict[str, ResearchHistory]:
        research_history = github_download(
            github_repository_info=state["github_repository_info"],
            github_client=self.github_client,
            file_path=self.research_file_path,
        )
        return {"research_history": research_history}

    @time_node("github_upload_subgraph", "_merge_history_node")
    def _merge_history_node(
        self, state: GithubUploadSubgraphState
    ) -> dict[str, ResearchHistory]:
        merged_history = merge_history(
            old=state["research_history"],
            new=state["cumulative_data"],
        )
        return {"research_history": merged_history}

    @time_node("github_upload_subgraph", "_github_upload_node")
    def _github_upload_node(self, state: GithubUploadSubgraphState) -> dict[str, Any]:
        commit_message = (
            f"[subgraph: {state['subgraph_name']}] run at {datetime.now().isoformat()}"
        )

        is_github_upload_success = github_upload(
            github_repository_info=state["github_repository_info"],
            github_client=self.github_client,
            research_history=state["research_history"],
            file_path=self.research_file_path,
            commit_message=commit_message,
        )
        return {"is_github_upload_success": is_github_upload_success}

    def build_graph(self):
        sg = StateGraph(GithubUploadSubgraphState)
        sg.add_node("github_download", self._github_download_node)
        sg.add_node("merge_history", self._merge_history_node)
        sg.add_node("github_upload", self._github_upload_node)

        sg.add_edge(START, "github_download")
        sg.add_edge("github_download", "merge_history")
        sg.add_edge("merge_history", "github_upload")
        sg.add_edge("github_upload", END)
        return sg.compile()

    def run(self, state: dict[str, Any], config: dict | None = None) -> dict[str, Any]:
        return asyncio.run(self.arun(state, config=config))

    async def arun(
        self, state: dict[str, Any], config: dict | None = None
    ) -> dict[str, Any]:
        input_state_keys = self.InputState.__annotations__.keys()
        input_state = {k: state[k] for k in input_state_keys if k in state}

        # NOTE: Excluding keys that are not uploaded
        filtered_state = {}
        for k, v in state.items():
            if k in ["subgraph_name", "github_repository_info"]:
                continue
            filtered_state[k] = v
        cumulative_data = ResearchHistory.model_validate(filtered_state)
        input_state["cumulative_data"] = cumulative_data

        config = config or {"recursion_limit": 200}
        _ = await self.build_graph().ainvoke(input_state, config=config)

        state["subgraph_name"] = self.__class__.__name__
        return state


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="GithubUploadSubgraph")
    parser.add_argument("github_repository", help="Your GitHub repository")
    parser.add_argument(
        "branch_name", help="Your branch name in your GitHub repository"
    )

    args = parser.parse_args()

    queries = ["diffusion model"]
    subgraph_name = "RetrievePaperFromQuerySubgraph"
    github_repository_info = GitHubRepositoryInfo(
        github_owner=args.github_repository.split("/")[0],
        repository_name=args.github_repository.split("/")[1],
        branch_name=args.branch_name,
    )
    state = {
        "github_repository_info": github_repository_info,
        "subgraph_name": subgraph_name,
        "queries": queries,
    }

    GithubUploadSubgraph().run(state)
