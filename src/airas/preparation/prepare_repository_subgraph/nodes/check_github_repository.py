from logging import getLogger

from airas.utils.api_client.github_client import GithubClient, GithubClientError

logger = getLogger(__name__)


# NOTE：API Documentation
# https://docs.github.com/ja/rest/repos/repos?apiVersion=2022-11-28#get-a-repository


def check_github_repository(
    github_owner: str, 
    repository_name: str, 
    client: GithubClient | None = None, 
    ) -> bool:
    if client is None:
        client = GithubClient()

    try:
        response = client.get_repository(
            github_owner=github_owner,
            repository_name=repository_name,
        )
        return response is not None
    except GithubClientError as e:
        logger.warning(f"Repository check failed: {e}")
        return False