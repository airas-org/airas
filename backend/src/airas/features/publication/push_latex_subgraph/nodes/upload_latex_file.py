import logging

from airas.services.api_client.github_client import GithubClient
from airas.types.github import GitHubConfig
from airas.types.latex import LATEX_TEMPLATE_NAME

logger = logging.getLogger(__name__)


def upload_latex_file(
    github_config: GitHubConfig,
    latex_text: str,
    latex_template_name: LATEX_TEMPLATE_NAME,
    github_client: GithubClient,
    paper_name: str = "main",
) -> bool:
    is_uploaded = github_client.commit_file_bytes(
        github_owner=github_config.github_owner,
        repository_name=github_config.repository_name,
        branch_name=github_config.branch_name,
        file_path=f".research/latex/{latex_template_name}/{paper_name}.tex",
        file_content=latex_text.encode("utf-8"),
        commit_message=f"Upload LaTeX file: {paper_name}.tex",
    )

    return is_uploaded
