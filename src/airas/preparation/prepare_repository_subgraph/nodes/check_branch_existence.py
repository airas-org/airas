from logging import getLogger
from typing import Literal

from airas.utils.api_client.github_client import GithubClient

logger = getLogger(__name__)
DEVICETYPE = Literal["cpu", "gpu"]


def check_branch_existence(
    github_owner: str, 
    repository_name: str, 
    branch_name: str, 
    client: GithubClient | None = None, 
) -> str | None:
    if client is None:
        client = GithubClient()
        
    response = client.get_branch(
        github_owner=github_owner,
        repository_name=repository_name,
        branch_name=branch_name,
    )
    if response is None:
        logger.warning(
            f"Branch '{branch_name}' not found in repository '{repository_name}'."
        )
        return None
    
    try:
        return response["commit"]["sha"]
    except KeyError:
        logger.warning(f"Unexpected response format: missing 'commit.sha'. Response: {response}")
        return None


if __name__ == "__main__":
    # Example usage
    github_owner = "auto-res2"
    repository_name = "test-branch"
    branch_name = "test"
    output = check_branch_existence(github_owner, repository_name, branch_name)
    print(output)
