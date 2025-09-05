from logging import getLogger

from airas.services.api_client.github_client import GithubClient
from airas.types.github import GitHubRepositoryInfo

logger = getLogger(__name__)


def prepare_images_for_html(
    github_repository: GitHubRepositoryInfo,
    workflow_file: str = "prepare_images_for_html.yml",
    client: GithubClient | None = None,
) -> str | None:
    if client is None:
        client = GithubClient()

    github_owner = github_repository.github_owner
    repository_name = github_repository.repository_name
    branch_name = github_repository.branch_name or "main"

    try:
        success = client.create_workflow_dispatch(
            github_owner,
            repository_name,
            workflow_file,
            ref=branch_name,
        )

        if success:
            relative_path = f"branches/{branch_name}/index.html"
            github_pages_url = (
                f"https://{github_owner}.github.io/{repository_name}/{relative_path}"
            )
            logger.info("Workflow dispatched successfully.")
            logger.info(
                f"GitHub Pages build triggered. HTML will be available at: {github_pages_url} "
                "(It may take a few minutes to reflect on GitHub Pages)"
            )
            return github_pages_url
        else:
            logger.error("Workflow dispatch failed")
            return None

    except Exception as e:
        logger.error(f"Failed to dispatch workflow: {e}")
        return None
