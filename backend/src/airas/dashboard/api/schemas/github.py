from pydantic import BaseModel, Field

from airas.core.types.github import GitHubConfig


class GitHubConfigRequest(BaseModel):
    """Request body schema for GitHub config (owner is resolved server-side)."""

    repository_name: str = Field(..., description="Name of the repository")
    branch_name: str = Field(..., description="Branch name")


class PushGitHubRequestBody(BaseModel):
    github_config: GitHubConfig
    push_files: dict[str, str]


class PushGitHubResponseBody(BaseModel):
    is_file_pushed: bool
    execution_time: dict[str, list[float]]
