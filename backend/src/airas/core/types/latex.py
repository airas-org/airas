from typing import Literal

from airas.core.types.github import GitHubRepositoryInfo

LATEX_TEMPLATE_NAME = Literal[
    "iclr2024",
    "agents4science_2025",
    "MDPI",
]

# Official LaTeX template repository
LATEX_TEMPLATE_REPOSITORY_INFO = GitHubRepositoryInfo(
    github_owner="airas-org",
    repository_name="airas-template",
    branch_name="main",
)
