from logging import getLogger
from typing import Literal

from airas.services.api_client.github_client import GithubClient
from airas.types.github import GitHubConfig

logger = getLogger(__name__)


def create_repository_from_template(
    github_config: GitHubConfig,
    github_client: GithubClient,
    template_owner: str,
    template_repo: str,
    include_all_branches: bool = True,
    is_github_repo_private: bool = False,
) -> Literal[True]:
    try:
        result = github_client.create_repository_from_template(
            github_owner=github_config.github_owner,
            repository_name=github_config.repository_name,
            template_owner=template_owner,
            template_repo=template_repo,
            include_all_branches=include_all_branches,
            private=is_github_repo_private,
        )
        if not result:
            error = (
                f"No repository created; received empty response for template "
                f"{template_owner}/{template_repo}"
            )
            logger.error(error)
            raise RuntimeError(error)

        print(
            f"Repository created from template: {template_owner}/{template_repo} -> {github_config.github_owner}/{github_config.repository_name}"
        )
        return True

    except Exception as e:
        logger.error(f"Unexpected error when creating from template: {e}")
        raise
