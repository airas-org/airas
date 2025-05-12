from logging import getLogger

from airas.utils.api_client.github_client import GithubClient

logger = getLogger(__name__)


def create_repository_from_template(
    github_owner: str,
    repository_name: str,
    template_owner: str,
    template_repo: str,
    include_all_branches: bool = True,
    private: bool = False,
    client: GithubClient | None = None,
) -> bool:
    if client is None:
        client = GithubClient()

    try:
        result = client.create_repository_from_template(
            github_owner=github_owner,
            repository_name=repository_name,
            template_owner=template_owner,
            template_repo=template_repo,
            include_all_branches=include_all_branches,
            private=private,
        )
        if result:
            logger.info(
                f"Repository created from template: {template_owner}/{template_repo} -> {github_owner}/{repository_name}"
            )
            return True
        else:
            logger.warning(
                f"No repository created; received empty response for template {template_owner}/{template_repo}"
            )
        return False
    except Exception as e:
        logger.error(f"Unexpected error when creating from template: {e}")
        raise
