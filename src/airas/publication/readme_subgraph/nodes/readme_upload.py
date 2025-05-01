import os
import base64

from airas.utils.api_request_handler import fetch_api_data, retry_request
from logging import getLogger

logger = getLogger(__name__)

GITHUB_PERSONAL_ACCESS_TOKEN = os.getenv("GITHUB_PERSONAL_ACCESS_TOKEN")


def _request_get_github_content(
    headers: dict,
    github_owner: str,
    repository_name: str,
    branch_name: str,
    repository_path: str,
) -> dict | None:
    url = f"https://api.github.com/repos/{github_owner}/{repository_name}/contents/{repository_path}"
    params = {
        "ref": f"{branch_name}",
    }
    return retry_request(
        fetch_api_data, url, headers=headers, params=params, method="GET"
    )


def _request_github_file_upload(
    headers: dict,
    github_owner: str,
    repository_name: str,
    branch_name: str,
    repository_path: str,
    encoded_data: str,
    sha: str | None,
):
    url = f"https://api.github.com/repos/{github_owner}/{repository_name}/contents/{repository_path}"
    data = {
        "message": "Research paper uploaded.",
        "branch": f"{branch_name}",
        "content": encoded_data,
    }
    if sha is not None:
        data["sha"] = sha
    return retry_request(fetch_api_data, url, headers=headers, data=data, method="PUT")


def _encoded_markdown_data(
    title: str,
    abstract: str,
    research_history_url: str,
    devin_url: str,
):
    markdown_text = f"""
# {title}
> ⚠️ **NOTE:** This research is an automatic research using Research Graph.
## Abstract
{abstract}

- [Research history]({research_history_url})
- [Devin execution log]({devin_url})"""
    encoded_markdown_data = base64.b64encode(markdown_text.encode("utf-8")).decode(
        "utf-8"
    )
    return encoded_markdown_data


def readme_upload(
    github_owner: str,
    repository_name: str,
    branch_name: str,
    title: str,
    abstract: str,
    devin_url: str,
) -> bool:
    headers = {
        "Accept": "application/vnd.github+json",
        "Authorization": f"Bearer {GITHUB_PERSONAL_ACCESS_TOKEN}",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    research_history_url = f"https://github.com/{github_owner}/{repository_name}/blob/{branch_name}/.research/research_history.json"

    encoded_markdown_data = _encoded_markdown_data(
        title,
        abstract,
        research_history_url,
        devin_url,
    )

    logger.info("README upload")
    readme_path = "README.md"
    response_readme = _request_get_github_content(
        headers=headers,
        github_owner=github_owner,
        repository_name=repository_name,
        branch_name=branch_name,
        repository_path=readme_path,
    )

    _request_github_file_upload(
        headers=headers,
        github_owner=github_owner,
        repository_name=repository_name,
        branch_name=branch_name,
        encoded_data=encoded_markdown_data,
        repository_path=readme_path,
        sha=response_readme["sha"] if response_readme is not None else None,
    )
    return True
