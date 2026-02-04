import logging

from langgraph.graph import END, START, StateGraph
from typing_extensions import TypedDict

from airas.core.execution_timers import ExecutionTimeState, time_node
from airas.core.logging_utils import setup_logging
from airas.core.types.github import GitHubConfig
from airas.infra.github_client import GithubClient
from airas.usecases.github.push_github_subgraph.nodes.push_files_to_branch import (
    push_files_to_github,
)

setup_logging()
logger = logging.getLogger(__name__)

record_execution_time = lambda f: time_node("push_code_subgraph")(f)  # noqa: E731


class PushGitHubSubgraphInputState(TypedDict):
    github_config: GitHubConfig
    push_files: dict[str, str]


class PushGitHubSubgraphOutputState(ExecutionTimeState):
    is_file_pushed: bool


class PushGitHubSubgraphState(
    PushGitHubSubgraphInputState,
    PushGitHubSubgraphOutputState,
):
    pass


class PushGitHubSubgraph:
    def __init__(
        self,
        github_client: GithubClient,
    ):
        self.github_client = github_client

    @record_execution_time
    def push_files_to_github(self, state: PushGitHubSubgraphState) -> dict[str, bool]:
        commit_message = "File push using AIRAS"

        success = push_files_to_github(
            github_config=state["github_config"],
            github_client=self.github_client,
            push_files=state["push_files"],
            commit_message=commit_message,
        )

        if not success:
            logger.error("Failed to push files to branch")
            raise RuntimeError("Failed to push files to GitHub branch")

        return {"is_file_pushed": success}

    def build_graph(self):
        graph_builder = StateGraph(
            PushGitHubSubgraphState,
            input_schema=PushGitHubSubgraphInputState,
            output_schema=PushGitHubSubgraphOutputState,
        )
        graph_builder.add_node("push_files_to_github", self.push_files_to_github)
        graph_builder.add_edge(START, "push_files_to_github")
        graph_builder.add_edge("push_files_to_github", END)
        return graph_builder.compile()
