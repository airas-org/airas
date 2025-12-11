import json
import logging

import httpx

from airas.services.api_client.github_client import GithubClient
from airas.types.github import GitHubConfig
from airas.types.research_history import ResearchHistory

logger = logging.getLogger(__name__)


def github_download(
    github_config: GitHubConfig,
    github_client: GithubClient,
    file_path: str = ".research/research_history.json",
) -> ResearchHistory:
    logger.info(
        f"[GitHub I/O] Download: {github_config.github_owner}/{github_config.repository_name}@{github_config.branch_name}:{file_path}"
    )

    try:
        blob = github_client.get_repository_content(
            github_owner=github_config.github_owner,
            repository_name=github_config.repository_name,
            file_path=file_path,
            branch_name=github_config.branch_name,
        )

        download_url = blob.get("download_url")
        if not download_url:
            logger.error("No download_url available for file")
            return ResearchHistory()

        logger.info(f"Downloading file directly: {download_url}")
        with httpx.Client() as client:
            response = client.get(download_url)
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
