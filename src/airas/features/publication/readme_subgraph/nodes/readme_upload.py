from logging import getLogger

from airas.services.api_client.github_client import GithubClient
from airas.types.github import GitHubRepositoryInfo

logger = getLogger(__name__)


def _build_markdown(
    title: str,
    abstract: str,
    research_history_url: str,
    devin_url: str | None,
    github_pages_url: str,
) -> str:
    links = [
        f"- [Research history]({research_history_url})",
        f"- [GitHub Pages]({github_pages_url})",
    ]

    if devin_url is not None:
        links.append(f"- [Devin execution log]({devin_url})")

    return f"""# {title}
> ⚠️ **NOTE:** This research is an automatic research using AIRAS.
## Abstract
{abstract}

{chr(10).join(links)}"""


def readme_upload(
    github_repository_info: GitHubRepositoryInfo,
    title: str,
    abstract: str,
    devin_url: str | None,
    github_pages_url: str,
    client: GithubClient | None = None,
) -> bool:
    if client is None:
        client = GithubClient()
    logger.info("Preparing README content for upload")

    research_history_url = (
        f"https://github.com/{github_repository_info.github_owner}/{github_repository_info.repository_name}"
        f"/blob/{github_repository_info.branch_name}/.research/research_history.json"
    )

    markdown = _build_markdown(
        title,
        abstract,
        research_history_url,
        devin_url,
        github_pages_url,
    )
    markdown_bytes = markdown.encode("utf-8")

    logger.info("Uploading README.md via GithubClient.commit_file_bytes")
    return client.commit_file_bytes(
        github_owner=github_repository_info.github_owner,
        repository_name=github_repository_info.repository_name,
        branch_name=github_repository_info.branch_name,
        file_path="README.md",
        file_content=markdown_bytes,
        commit_message="Research paper uploaded.",
    )
