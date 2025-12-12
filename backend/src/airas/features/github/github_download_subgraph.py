import logging

from langgraph.graph import END, START, StateGraph
from typing_extensions import TypedDict

from airas.features.github.nodes.github_download import github_download
from airas.services.api_client.github_client import GithubClient
from airas.types.github import GitHubConfig
from airas.types.research_history import ResearchHistory
from airas.utils.check_api_key import check_api_key
from airas.utils.execution_timers import ExecutionTimeState, time_node
from airas.utils.logging_utils import setup_logging

setup_logging()
logger = logging.getLogger(__name__)

record_execution_time = lambda f: time_node("github_download_subgraph")(f)  # noqa: E731


class GithubDownloadInputState(TypedDict):
    github_config: GitHubConfig


class GithubDownloadOutputState(ExecutionTimeState):
    research_history: ResearchHistory


class GithubDownloadSubgraphState(
    GithubDownloadInputState,
    GithubDownloadOutputState,
    total=False,
):
    pass


class GithubDownloadSubgraph:
    def __init__(self, github_client: GithubClient):
        check_api_key(
            github_personal_access_token_check=True,
        )
        self.research_file_path = ".research/research_history.json"
        self.github_client = github_client

    @record_execution_time
    def _download_history(
        self, state: GithubDownloadSubgraphState
    ) -> dict[str, ResearchHistory]:
        research_history = github_download(
            github_config=state["github_config"],
            github_client=self.github_client,
        )
        return {
            "research_history": research_history,
        }

    def build_graph(self):
        sg = StateGraph(
            GithubDownloadSubgraphState,
            input_schema=GithubDownloadInputState,
            output_schema=GithubDownloadOutputState,
        )
        sg.add_node("download_history", self._download_history)

        sg.add_edge(START, "download_history")
        sg.add_edge("download_history", END)
        return sg.compile()
