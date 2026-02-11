import io
import json
import logging
import zipfile

from langgraph.graph import END, START, StateGraph
from typing_extensions import TypedDict

from airas.core.execution_timers import ExecutionTimeState, time_node
from airas.core.logging_utils import setup_logging
from airas.core.types.github import GitHubConfig
from airas.infra.github_client import GithubClient

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
    async def _download_and_parse_artifact(
        self, state: DownloadGithubActionsArtifactsState
    ) -> dict[str, dict]:
        github_config = state["github_config"]
        workflow_run_id = state["workflow_run_id"]

        logger.info(
            f"Downloading artifact for workflow_run_id={workflow_run_id} "
            f"from {github_config.repository_name}"
        )

        # List all artifacts in the repository
        artifacts_response = self.github_client.list_repository_artifacts(
            github_owner=github_config.github_owner,
            repository_name=github_config.repository_name,
        )

        if not artifacts_response or "artifacts" not in artifacts_response:
            logger.error("No artifacts found in repository")
            return {"artifact_data": {}}

        artifacts = artifacts_response["artifacts"]

        # Filter artifacts by workflow_run.id
        target_artifact = None
        for artifact in artifacts:
            workflow_run = artifact.get("workflow_run")
            if workflow_run and workflow_run.get("id") == workflow_run_id:
                target_artifact = artifact
                break

        if not target_artifact:
            logger.warning(f"Artifact not found for workflow_run_id={workflow_run_id}")
            return {"artifact_data": {}}

        artifact_id = target_artifact["id"]
        logger.info(f"Found artifact: {target_artifact['name']} (id={artifact_id})")

        # Download artifact archive (zip file)
        zip_data = self.github_client.download_artifact_archive(
            github_owner=github_config.github_owner,
            repository_name=github_config.repository_name,
            artifact_id=artifact_id,
        )

        if not zip_data:
            logger.error(f"Failed to download artifact {artifact_id}")
            return {"artifact_data": {}}

        # Extract and parse JSON from zip
        try:
            artifact_data = self._extract_json_from_zip(zip_data)
            logger.info(f"Successfully parsed artifact data: {artifact_data}")
            return {"artifact_data": artifact_data}
        except Exception as e:
            logger.error(f"Failed to extract JSON from artifact: {e}")
            return {"artifact_data": {}}

    def _extract_json_from_zip(self, zip_data: bytes) -> dict:
        """Extract and parse JSON file from zip archive"""
        with zipfile.ZipFile(io.BytesIO(zip_data)) as zf:
            # Get list of files in zip
            file_list = zf.namelist()
            logger.info(f"Files in artifact zip: {file_list}")

            # Look for JSON file (assume first .json file)
            json_file = None
            for filename in file_list:
                if filename.endswith(".json"):
                    json_file = filename
                    break

            if not json_file:
                raise ValueError("No JSON file found in artifact")

            # Read and parse JSON
            with zf.open(json_file) as f:
                content = f.read()
                return json.loads(content)

    def build_graph(self):
        graph_builder = StateGraph(
            DownloadGithubActionsArtifactsState,
            input_schema=DownloadGithubActionsArtifactsInputState,
            output_schema=DownloadGithubActionsArtifactsOutputState,
        )

        graph_builder.add_node(
            "download_and_parse_artifact", self._download_and_parse_artifact
        )

        graph_builder.add_edge(START, "download_and_parse_artifact")
        graph_builder.add_edge("download_and_parse_artifact", END)

        return graph_builder.compile()
