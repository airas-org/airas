from logging import getLogger

from airas.services.api_client.github_client import GithubClient

logger = getLogger(__name__)


def _build_markdown(
    title: str, abstract: str, research_history_url: str, devin_url: str
) -> str:
    return f"""# {title}
> ⚠️ **NOTE:** This research is an automatic research using AIRAS.
## Abstract
{abstract}

- [Research history]({research_history_url})
- [Devin execution log]({devin_url})"""


def readme_upload(
    github_owner: str,
    repository_name: str,
    branch_name: str,
    title: str,
    abstract: str,
    devin_url: str,
    client: GithubClient | None = None,
) -> bool:
    if client is None:
        client = GithubClient()
    logger.info("Preparing README content for upload")

    research_history_url = (
        f"https://github.com/{github_owner}/{repository_name}"
        f"/blob/{branch_name}/.research/research_history.json"
    )

    markdown = _build_markdown(
        title,
        abstract,
        research_history_url,
        devin_url,
    )
    markdown_bytes = markdown.encode("utf-8")

    logger.info("Uploading README.md via GithubClient.commit_file_bytes")
    return client.commit_file_bytes(
        github_owner=github_owner,
        repository_name=repository_name,
        branch_name=branch_name,
        file_path="README.md",
        file_content=markdown_bytes,
        commit_message="Research paper uploaded.",
    )
