import logging

from langgraph.graph import END, START, StateGraph
from typing_extensions import TypedDict

from airas.core.execution_timers import ExecutionTimeState, time_node
from airas.core.logging_utils import setup_logging
from airas.core.types.github import GitHubConfig
from airas.infra.github_client import GithubClient
from airas.usecases.github.nodes.download_artifact import download_and_parse_artifact

setup_logging()
logger = logging.getLogger(__name__)

record_execution_time = lambda f: time_node("download_github_actions_artifacts")(f)  # noqa: E731


class DownloadGithubActionsArtifactsInputState(TypedDict):
    github_config: GitHubConfig
    workflow_run_id: int


class DownloadGithubActionsArtifactsOutputState(ExecutionTimeState):
    artifact_data: dict  # Parsed JSON content from the artifact


class DownloadGithubActionsArtifactsState(
    DownloadGithubActionsArtifactsInputState,
    DownloadGithubActionsArtifactsOutputState,
    total=False,
):
    pass


class DownloadGithubActionsArtifactsSubgraph:
    def __init__(
        self,
        github_client: GithubClient,
    ):
        self.github_client = github_client

    @record_execution_time
    async def _download_and_parse_artifact_node(
        self, state: DownloadGithubActionsArtifactsState
    ) -> dict[str, dict]:
        artifact_data = await download_and_parse_artifact(
            github_client=self.github_client,
            github_config=state["github_config"],
            workflow_run_id=state["workflow_run_id"],
        )
        return {"artifact_data": artifact_data}

    def build_graph(self):
        graph_builder = StateGraph(
            DownloadGithubActionsArtifactsState,
            input_schema=DownloadGithubActionsArtifactsInputState,
            output_schema=DownloadGithubActionsArtifactsOutputState,
        )

        graph_builder.add_node(
            "download_and_parse_artifact", self._download_and_parse_artifact_node
        )

        graph_builder.add_edge(START, "download_and_parse_artifact")
        graph_builder.add_edge("download_and_parse_artifact", END)

        return graph_builder.compile()
