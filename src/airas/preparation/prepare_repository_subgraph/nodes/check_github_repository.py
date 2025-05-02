from logging import getLogger
from airas.utils.api_client.github_client import GithubClient

logger = getLogger(__name__)


# NOTE：API Documentation
# https://docs.github.com/ja/rest/repos/repos?apiVersion=2022-11-28#get-a-repository


def check_github_repository(github_owner: str, repository_name: str) -> bool | None:
    client = GithubClient()
    return client.check_repository_existence(
        repository_owner=github_owner,
        repository_name=repository_name,
    )


if __name__ == "__main__":
    # Example usage
    github_owner = "auto-res2"
    repository_name = "gpu-repository"
    github_owner = "auto-res"
    repository_name = "cpu-repository"
    check_github_repository(github_owner, repository_name)
