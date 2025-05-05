from logging import getLogger
from typing import Literal, TypeAlias

from airas.utils.api_client.github_client import GithubClient

logger = getLogger(__name__)
DEVICETYPE: TypeAlias = Literal["cpu", "gpu"]

# NOTE：API Documentation
# https://docs.github.com/ja/rest/repos/forks?apiVersion=2022-11-28#create-a-fork


def fork_repository(
    repository_name: str,
    # NOTE:Make it possible to respond simply by rewriting run_experiment.yml.
    device_type: DEVICETYPE,
    organization: str = "",
) -> bool:
    client = GithubClient()
    return client.fork_repository(
        repository_name=repository_name,
        device_type=device_type,
        organization=organization,
    )


if __name__ == "__main__":
    # Example usage
    repository_name = "test-branch"
    organization = "auto-res2"  # or "" for no organization
    fork_repository(repository_name, "gpu", organization)
