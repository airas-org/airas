import base64
import json
import logging
from typing import Any

from airas.services.api_client.github_client import GithubClient
from airas.types.github import GitHubRepositoryInfo

logger = logging.getLogger(__name__)


def github_download(
    github_repository_info: GitHubRepositoryInfo,
    file_path: str = ".research/research_history.json",
    client: GithubClient | None = None,
) -> dict[str, Any]:
    if client is None:
        client = GithubClient()
    logger.info(
        f"[GitHub I/O] Download: {github_repository_info.github_owner}/{github_repository_info.repository_name}@{github_repository_info.branch_name}:{file_path}"
    )

    try:
        blob = client.get_repository_content(
            github_owner=github_repository_info.github_owner,
            repository_name=github_repository_info.repository_name,
            file_path=file_path,
            branch_name=github_repository_info.branch_name,
        )
        raw = base64.b64decode(blob["content"])
        return json.loads(raw) if raw else {}
    except FileNotFoundError as e:
        logger.error(f"State file not found – start with empty dict: {e}")
        raise
