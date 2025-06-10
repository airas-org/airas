from logging import getLogger
from typing import Literal

from airas.utils.api_client.github_client import GithubClient

logger = getLogger(__name__)
DEVICETYPE = Literal["cpu", "gpu"]

# NOTE：API Documentation
# https://docs.github.com/ja/rest/git/refs?apiVersion=2022-11-28#create-a-reference


def create_branch(
    github_owner: str,
    repository_name: str,
    branch_name: str,
    main_sha: str,
    client: GithubClient | None = None, 
) -> Literal[True]:
    if client is None:
        client = GithubClient()

    response = client.create_branch(
        github_owner=github_owner,
        repository_name=repository_name,
        branch_name=branch_name,
        from_sha=main_sha,
    )
    if not response:
        raise RuntimeError(f"Failed to create branch '{branch_name}' from '{main_sha}' in {github_owner}/{repository_name}")
    
    print(f"Branch '{branch_name}' created in repository '{github_owner}/{repository_name}'")
    return response


if __name__ == "__main__":
    # Example usage
    github_owner = "auto-res2"
    repository_name = "test-branch"
    branch_name = "test"
    sha = "0b4ffd87d989e369a03fce523be014bc6cf75ea8"
    output = create_branch(
        github_owner=github_owner,
        repository_name=repository_name,
        branch_name=branch_name,
        main_sha=sha,  # You need to provide the SHA of the commit you want to branch from
    )
    print(output)
