import base64
import logging
from typing import cast

from airas.services.api_client.github_client import GithubClient
from airas.types.github import GitHubRepositoryInfo

logger = logging.getLogger(__name__)


def retrieve_github_repository_file(
    github_repository: GitHubRepositoryInfo,
    file_path: str,
    client: GithubClient | None = None,
) -> str:
    client = client or GithubClient()
    file_data = client.get_repository_content(
        github_owner=github_repository.github_owner,
        repository_name=github_repository.repository_name,
        branch_name=github_repository.branch_name,
        file_path=file_path,
    )

    file_data_dict = cast(dict, file_data)
    decoded_bytes = base64.b64decode(file_data_dict["content"])
    latex_content = decoded_bytes.decode("utf-8")
    return latex_content


if __name__ == "__main__":
    github_repository = {
        "github_owner": "auto-res2",
        "repository_name": "tanaka-20250729-v3",
        "branch_name": "main",
    }
    latex_template = retrieve_github_repository_file(
        github_repository=github_repository,
        file_path=".research/latex/iclr2024/template.tex",
    )
    print(latex_template)
