from logging import getLogger
from typing import Literal

from airas.utils.api_client.github_client import GithubClient

logger = getLogger(__name__)
DEVICETYPE = Literal["cpu", "gpu"]

# NOTE：API Documentation
# https://docs.github.com/ja/rest/branches/branches?apiVersion=2022-11-28#get-a-branch


def retrieve_main_branch_sha(
    github_owner: str,
    repository_name: str,
) -> str:
    client = GithubClient()
    sha = client.check_branch_existence(
        github_owner=github_owner,
        repository_name=repository_name,
        branch_name="main",
    )
    if sha is None:
        raise RuntimeError(f"Failed to retrieve SHA for 'main' branch of {github_owner}/{repository_name}")
    return sha


if __name__ == "__main__":
    # Example usage
    github_owner = "auto-res2"
    repository_name = "test-branch"
    branch_name = "test"
    output = retrieve_main_branch_sha(github_owner, repository_name)
    print(output)
