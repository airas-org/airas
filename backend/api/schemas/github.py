from pydantic import BaseModel

from airas.core.types.github import GitHubConfig


class PushGitHubRequestBody(BaseModel):
    github_config: GitHubConfig
    push_files: dict[str, str]


class PushGitHubResponseBody(BaseModel):
    is_file_pushed: bool
    execution_time: dict[str, list[float]]
