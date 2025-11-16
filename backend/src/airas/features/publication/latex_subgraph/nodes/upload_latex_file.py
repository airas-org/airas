import logging

from airas.services.api_client.github_client import GithubClient
from airas.types.github import GitHubRepositoryInfo
from airas.types.latex import LATEX_TEMPLATE_NAME

logger = logging.getLogger(__name__)


def upload_latex_file(
    github_repository: GitHubRepositoryInfo,
    latex_text: str,
    latex_template_name: LATEX_TEMPLATE_NAME,
    github_client: GithubClient,
) -> bool:
    is_uploaded = github_client.commit_file_bytes(
        github_owner=github_repository.github_owner,
        repository_name=github_repository.repository_name,
        branch_name=github_repository.branch_name,
        file_path=f".research/latex/{latex_template_name}/paper.tex",
        file_content=latex_text.encode("utf-8"),
        commit_message="Upload LaTeX file",
    )

    return is_uploaded


if __name__ == "__main__":
    # Example usage
    github_repository = {
        "github_owner": "auto-res2",
        "repository_name": "tanaka-20250803-v3",
        "branch_name": "main",
    }
    success = upload_latex_file(
        github_repository=github_repository,
        latex_text="\\documentclass{article}\n\\begin{document}\nHello, World!\n\\end{document}",
        latex_template_name="iclr2024",
    )
    print(f"Upload successful: {success}")
