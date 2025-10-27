from logging import getLogger

from dependency_injector.wiring import Provide, inject

from airas.services.api_client.api_clients_container import APIClientsContainer
from airas.services.api_client.github_client import GithubClient
from airas.types.github import GitHubRepositoryInfo

logger = getLogger(__name__)


@inject
def check_branch_existence(
    github_repository_info: GitHubRepositoryInfo,
    client: GithubClient = Provide[APIClientsContainer.github_client],
) -> str | None:
    response = client.get_branch(
        github_owner=github_repository_info.github_owner,
        repository_name=github_repository_info.repository_name,
        branch_name=github_repository_info.branch_name,
    )
    if response is None:
        logger.warning(
            f"Branch '{github_repository_info.branch_name}' not found in repository '{github_repository_info.repository_name}'."
        )
        return None

    try:
        return response["commit"]["sha"]
    except KeyError:
        logger.warning(
            f"Unexpected response format: missing 'commit.sha'. Response: {response}"
        )
        return None


if __name__ == "__main__":
    # Example usage
    github_repository_info = GitHubRepositoryInfo(
        github_owner="auto-res2", repository_name="test-branch", branch_name="test"
    )
    output = check_branch_existence(github_repository_info)
    print(output)
