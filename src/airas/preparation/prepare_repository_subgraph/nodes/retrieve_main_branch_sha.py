from typing import Literal
from logging import getLogger
from airas.utils.api_client.github_client import GithubClient

logger = getLogger(__name__)
DEVICETYPE = Literal["cpu", "gpu"]

# NOTE：API Documentation
# https://docs.github.com/ja/rest/branches/branches?apiVersion=2022-11-28#get-a-branch


def retrieve_main_branch_sha(
    github_owner: str,
    repository_name: str,
) -> str | None:
    client = GithubClient()
    sha = client.check_branch_existence(
        repository_owner=github_owner,
        repository_name=repository_name,
        branch_name="main",
        raise_if_missing=True,
    )
    return sha


if __name__ == "__main__":
    # Example usage
    github_owner = "auto-res2"
    repository_name = "test-branch"
    branch_name = "test"
    output = retrieve_main_branch_sha(github_owner, repository_name)
    print(output)
