from logging import getLogger
from typing import Literal

from airas.services.api_client.github_client import GithubClient

logger = getLogger(__name__)
DEVICETYPE = Literal["cpu", "gpu"]


def retrieve_main_branch_sha(
    github_owner: str,
    repository_name: str,
    client: GithubClient | None = None,
) -> str:
    if client is None:
        client = GithubClient()

    response = client.get_branch(
        github_owner=github_owner,
        repository_name=repository_name,
        branch_name="main",
    )
    try:
        sha = response["commit"]["sha"]
    except (TypeError, KeyError):
        error_msg = f"Failed to retrieve SHA for 'main' branch of {github_owner}/{repository_name}"
        raise RuntimeError(error_msg)  # noqa: B904

    if not sha:
        raise RuntimeError(
            f"Empty SHA for 'main' branch of {github_owner}/{repository_name}"
        )
    return sha


if __name__ == "__main__":
    # Example usage
    github_owner = "auto-res2"
    repository_name = "test-branch"
    branch_name = "test"
    output = retrieve_main_branch_sha(github_owner, repository_name)
    print(output)
