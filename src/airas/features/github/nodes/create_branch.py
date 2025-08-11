from logging import getLogger
from typing import Literal

from airas.services.api_client.github_client import GithubClient
from airas.types.github import GitHubRepositoryInfo

logger = getLogger(__name__)
DEVICETYPE = Literal["cpu", "gpu"]

# NOTE：API Documentation
# https://docs.github.com/ja/rest/git/refs?apiVersion=2022-11-28#create-a-reference


def create_branch(
    github_repository_info: GitHubRepositoryInfo,
    sha: str,
    client: GithubClient | None = None,
) -> Literal[True]:
    if client is None:
        client = GithubClient()

    response = client.create_branch(
        github_owner=github_repository_info.github_owner,
        repository_name=github_repository_info.repository_name,
        branch_name=github_repository_info.branch_name,
        from_sha=sha,
    )
    if not response:
        raise RuntimeError(
            f"Failed to create branch '{github_repository_info.branch_name}' from '{sha}' in {github_repository_info.github_owner}/{github_repository_info.repository_name}"
        )

    print(
        f"Branch '{github_repository_info.branch_name}' created in repository '{github_repository_info.github_owner}/{github_repository_info.repository_name}'"
    )
    return response


if __name__ == "__main__":
    # Example usage
    github_repository_info = GitHubRepositoryInfo(
        github_owner="auto-res2", repository_name="test-branch", branch_name="test"
    )
    sha = "0b4ffd87d989e369a03fce523be014bc6cf75ea8"
    output = create_branch(
        github_repository_info=github_repository_info,
        sha=sha,
    )
    print(output)
