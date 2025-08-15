import json
import logging
from typing import Any

import requests

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

        download_url = blob.get("download_url")
        if not download_url:
            logger.error("No download_url available for file")
            return {}

        logger.info(f"Downloading file directly: {download_url}")
        response = requests.get(download_url)
        response.raise_for_status()
        raw = response.content

        if not raw:
            logger.warning("Raw content is empty, returning empty dict")
            return {}

        decoded_content = json.loads(raw)
        return decoded_content

    except FileNotFoundError as e:
        logger.error(f"State file not found – start with empty dict: {e}")
        raise


if __name__ == "__main__":
    github_repository_info = GitHubRepositoryInfo(
        github_owner="auto-res2",
        repository_name="experiment_matsuzawa_colab_2",
        branch_name="develop_3",
    )

    result = github_download(github_repository_info)
    print(f"result: {result.keys()}")
