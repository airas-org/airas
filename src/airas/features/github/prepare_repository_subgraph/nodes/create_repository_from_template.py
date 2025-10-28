from logging import getLogger
from typing import Literal

from dependency_injector.wiring import Provide, inject

from airas.services.api_client.api_clients_container import SyncContainer
from airas.services.api_client.github_client import GithubClient
from airas.types.github import GitHubRepositoryInfo

logger = getLogger(__name__)


@inject
def create_repository_from_template(
    github_repository_info: GitHubRepositoryInfo,
    template_owner: str,
    template_repo: str,
    include_all_branches: bool = True,
    private: bool = False,
    client: GithubClient = Provide[SyncContainer.github_client],
) -> Literal[True]:
    try:
        result = client.create_repository_from_template(
            github_owner=github_repository_info.github_owner,
            repository_name=github_repository_info.repository_name,
            template_owner=template_owner,
            template_repo=template_repo,
            include_all_branches=include_all_branches,
            private=private,
        )
        if not result:
            error = (
                f"No repository created; received empty response for template "
                f"{template_owner}/{template_repo}"
            )
            logger.error(error)
            raise RuntimeError(error)

        print(
            f"Repository created from template: {template_owner}/{template_repo} -> {github_repository_info.github_owner}/{github_repository_info.repository_name}"
        )
        return True

    except Exception as e:
        logger.error(f"Unexpected error when creating from template: {e}")
        raise
