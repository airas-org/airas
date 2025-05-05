from logging import getLogger
from typing import Literal

from airas.utils.api_client.github_client import GithubClient

logger = getLogger(__name__)
DEVICETYPE = Literal["cpu", "gpu"]

# NOTE：API Documentation
# https://docs.github.com/ja/rest/branches/branches?apiVersion=2022-11-28#get-a-branch


def check_branch_existence(
    github_owner: str, repository_name: str, branch_name: str
) -> str | None:
    client = GithubClient()
    sha = client.check_branch_existence(
        repository_owner=github_owner,
        repository_name=repository_name,
        branch_name=branch_name,
    )
    return sha


if __name__ == "__main__":
    # Example usage
    github_owner = "auto-res2"
    repository_name = "test-branch"
    branch_name = "test"
    output = check_branch_existence(github_owner, repository_name, branch_name)
    print(output)
