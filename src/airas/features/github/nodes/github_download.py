import json
import logging

import requests
from dependency_injector.wiring import Provide, inject

from airas.services.api_client.api_clients_container import api_clients_container
from airas.services.api_client.github_client import GithubClient
from airas.types.github import GitHubRepositoryInfo
from airas.types.research_history import ResearchHistory

logger = logging.getLogger(__name__)


@inject
def github_download(
    github_repository_info: GitHubRepositoryInfo,
    file_path: str = ".research/research_history.json",
    client: GithubClient = Provide[api_clients_container.github_client],
) -> ResearchHistory:
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
            return ResearchHistory()

        logger.info(f"Downloading file directly: {download_url}")
        response = requests.get(download_url)
        response.raise_for_status()
        raw = response.content

        if not raw:
            logger.warning("Raw content is empty, returning empty ResearchHistory")
            return ResearchHistory()

        # Parse JSON and convert to ResearchHistory
        try:
            decoded_dict = json.loads(raw)
            research_history = ResearchHistory.model_validate(decoded_dict)
            return research_history
        except Exception as e:
            logger.warning(
                f"Failed to convert to ResearchHistory: {e}, returning empty ResearchHistory"
            )
            return ResearchHistory()

    except FileNotFoundError as e:
        logger.error(f"State file not found – returning empty ResearchHistory: {e}")
        return ResearchHistory()
