import logging
from datetime import datetime

from langgraph.graph import END, START, StateGraph
from typing_extensions import TypedDict

from airas.features.github.nodes.github_download import github_download
from airas.features.github.nodes.github_upload import github_upload
from airas.features.github.nodes.merge_history import merge_history
from airas.services.api_client.github_client import GithubClient
from airas.types.github import GitHubConfig
from airas.types.research_history import ResearchHistory
from airas.utils.check_api_key import check_api_key
from airas.utils.execution_timers import ExecutionTimeState, time_node
from airas.utils.logging_utils import setup_logging

setup_logging()
logger = logging.getLogger(__name__)
record_execution_time = lambda f: time_node("github_upload_subgraph")(f)  # noqa: E731


class GithubUploadInputState(TypedDict):
    github_config: GitHubConfig
    research_history: ResearchHistory
    commit_message: str | None


class GithubUploadOutputState(ExecutionTimeState):
    is_github_upload: bool


class GithubUploadSubgraphState(
    GithubUploadInputState,
    GithubUploadOutputState,
    total=False,
):
    downloaded_history: ResearchHistory


class GithubUploadSubgraph:
    def __init__(self, github_client: GithubClient):
        check_api_key(
            github_personal_access_token_check=True,
        )
        self.research_file_path = ".research/research_history.json"
        self.github_client = github_client

    @record_execution_time
    def _download_history(
        self, state: GithubUploadSubgraphState
    ) -> dict[str, ResearchHistory]:
        downloaded_history = github_download(
            github_config=state["github_config"],
            github_client=self.github_client,
            file_path=self.research_file_path,
        )
        return {"downloaded_history": downloaded_history}

    @record_execution_time
    def _merge_history(
        self, state: GithubUploadSubgraphState
    ) -> dict[str, ResearchHistory]:
        merged_history = merge_history(
            old=state["downloaded_history"],
            new=state["research_history"],
        )
        return {"research_history": merged_history}

    @record_execution_time
    def _upload_history(self, state: GithubUploadSubgraphState) -> dict[str, bool]:
        default_commit_message = (
            f"Update research history at {datetime.now().isoformat()}"
        )

        is_github_upload = github_upload(
            github_config=state["github_config"],
            github_client=self.github_client,
            research_history=state["research_history"],
            file_path=self.research_file_path,
            commit_message=state.get("commit_message", default_commit_message),
        )
        return {"is_github_upload": is_github_upload}

    def build_graph(self):
        sg = StateGraph(
            GithubUploadSubgraphState,
            input_schema=GithubUploadInputState,
            output_schema=GithubUploadOutputState,
        )
        sg.add_node("download_history", self._download_history)
        sg.add_node("merge_history", self._merge_history)
        sg.add_node("upload_history", self._upload_history)

        sg.add_edge(START, "download_history")
        sg.add_edge("download_history", "merge_history")
        sg.add_edge("merge_history", "upload_history")
        sg.add_edge("upload_history", END)
        return sg.compile()
