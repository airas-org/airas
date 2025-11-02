from logging import getLogger

from dependency_injector.wiring import Provide, inject

from airas.services.api_client.api_clients_container import SyncContainer
from airas.services.api_client.github_client import GithubClient
from airas.types.github import GitHubRepositoryInfo

logger = getLogger(__name__)


@inject
def retrieve_main_branch_sha(
    github_repository_info: GitHubRepositoryInfo,
    client: GithubClient = Provide[SyncContainer.github_client],
) -> str:
    response = client.get_branch(
        github_owner=github_repository_info.github_owner,
        repository_name=github_repository_info.repository_name,
        branch_name="main",
    )

    if not response or not isinstance(response, dict):
        raise RuntimeError(
            f"Failed to retrieve branch info for 'main' branch of {github_repository_info.github_owner}/{github_repository_info.repository_name}"
        )

    try:
        sha = response["commit"]["sha"]
    except (TypeError, KeyError):
        msg = f"Invalid response format for 'main' branch of {github_repository_info.github_owner}/{github_repository_info.repository_name}"
        raise RuntimeError(msg)  # noqa: B904

    if not sha:
        raise RuntimeError(
            f"Empty SHA for 'main' branch of {github_repository_info.github_owner}/{github_repository_info.repository_name}"
        )
    return sha


if __name__ == "__main__":
    # Example usage
    github_repository_info = GitHubRepositoryInfo(
        github_owner="auto-res2", repository_name="test-branch", branch_name="test"
    )
    output = retrieve_main_branch_sha(github_repository_info)
    print(output)
