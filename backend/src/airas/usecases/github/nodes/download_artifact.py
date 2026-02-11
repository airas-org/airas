import io
import json
import logging
import zipfile

from airas.core.types.github import GitHubConfig
from airas.infra.github_client import GithubClient

logger = logging.getLogger(__name__)


def _extract_json_from_zip(zip_data: bytes) -> dict:
    with zipfile.ZipFile(io.BytesIO(zip_data)) as zf:
        file_list = zf.namelist()
        logger.info(f"Files in artifact zip: {file_list}")

        json_file = None
        for filename in file_list:
            if filename.endswith(".json"):
                json_file = filename
                break

        if not json_file:
            raise ValueError("No JSON file found in artifact")

        with zf.open(json_file) as f:
            content = f.read()
            return json.loads(content)


async def download_and_parse_artifact(
    github_client: GithubClient,
    github_config: GitHubConfig,
    workflow_run_id: int,
) -> dict:
    logger.info(
        f"Downloading artifact for workflow_run_id={workflow_run_id} "
        f"from {github_config.repository_name}"
    )

    artifacts_response = github_client.list_repository_artifacts(
        github_owner=github_config.github_owner,
        repository_name=github_config.repository_name,
    )

    if not artifacts_response or "artifacts" not in artifacts_response:
        logger.error("No artifacts found in repository")
        return {}

    artifacts = artifacts_response["artifacts"]

    target_artifact = None
    for artifact in artifacts:
        workflow_run = artifact.get("workflow_run")
        if workflow_run and workflow_run.get("id") == workflow_run_id:
            target_artifact = artifact
            break

    if not target_artifact:
        logger.warning(f"Artifact not found for workflow_run_id={workflow_run_id}")
        return {}

    artifact_id = target_artifact["id"]
    logger.info(f"Found artifact: {target_artifact['name']} (id={artifact_id})")

    zip_data = github_client.download_artifact_archive(
        github_owner=github_config.github_owner,
        repository_name=github_config.repository_name,
        artifact_id=artifact_id,
    )

    if not zip_data:
        logger.error(f"Failed to download artifact {artifact_id}")
        return {}

    try:
        artifact_data = _extract_json_from_zip(zip_data)
        if isinstance(artifact_data, dict):
            logger.info(
                f"Successfully parsed artifact data (keys={list(artifact_data.keys())}, key_count={len(artifact_data)})"
            )
        else:
            logger.info(
                f"Successfully parsed artifact data (type={type(artifact_data).__name__})"
            )
        logger.debug(f"Artifact data detail: {artifact_data}")
        return artifact_data
    except Exception as e:
        logger.error(f"Failed to extract JSON from artifact: {e}")
        return {}
