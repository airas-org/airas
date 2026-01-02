import base64
import logging
from typing import cast

from airas.core.types.github import GitHubRepositoryInfo
from airas.infra.github_client import GithubClient

logger = logging.getLogger(__name__)


def retrieve_github_repository_file(
    github_repository: GitHubRepositoryInfo,
    file_path: str,
    github_client: GithubClient,
) -> str:
    file_data = github_client.get_repository_content(
        github_owner=github_repository.github_owner,
        repository_name=github_repository.repository_name,
        branch_name=github_repository.branch_name,
        file_path=file_path,
    )

    file_data_dict = cast(dict, file_data)
    decoded_bytes = base64.b64decode(file_data_dict["content"])
    content = decoded_bytes.decode("utf-8")
    return content
