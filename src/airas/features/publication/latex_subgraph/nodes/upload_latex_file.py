import logging

from airas.services.api_client.github_client import GithubClient
from airas.types.latex import LATEX_TEMPLATE_NAME

logger = logging.getLogger(__name__)


def upload_latex_file(
    github_owner: str,
    repository_name: str,
    branch_name: str,
    latex_text: str,
    latex_template_name: LATEX_TEMPLATE_NAME,
) -> bool:
    client = GithubClient()

    is_uploaded = client.commit_file_bytes(
        github_owner=github_owner,
        repository_name=repository_name,
        branch_name=branch_name,
        file_path=f".research/latex/{latex_template_name}/paper.tex",
        file_content=latex_text.encode("utf-8"),
        commit_message="Upload LaTeX file",
    )

    return is_uploaded


if __name__ == "__main__":
    # Example usage
    success = upload_latex_file(
        github_owner="auto-res2",
        repository_name="tanaka-20250803-v3",
        branch_name="main",
        latex_text="\\documentclass{article}\n\\begin{document}\nHello, World!\n\\end{document}",
        latex_template_name="iclr2024",
    )
    print(f"Upload successful: {success}")
