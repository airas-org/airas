import logging

from airas.services.api_client.github_client import GithubClient
from airas.types.github import GitHubRepositoryInfo

logger = logging.getLogger(__name__)


def upload_html(
    github_repository: GitHubRepositoryInfo,
    full_html: str,
    github_client: GithubClient,
    upload_branch: str = "gh-pages",
    html_filename: str = "index.html",
) -> bool:
    try:
        branch_name = github_repository.branch_name
        file_path = f"branches/{branch_name}/{html_filename}"

        success = github_client.commit_file_bytes(
            github_owner=github_repository.github_owner,
            repository_name=github_repository.repository_name,
            branch_name=upload_branch,
            file_path=file_path,
            file_content=full_html.encode("utf-8"),
            commit_message=f"Upload HTML for branch {branch_name}",
        )

        if success:
            logger.info(f"Successfully uploaded HTML to {upload_branch}/{file_path}")
        else:
            logger.error(f"Failed to upload HTML to {upload_branch}/{file_path}")

        return success

    except Exception as e:
        logger.error(f"Error uploading HTML: {e}")
        return False
