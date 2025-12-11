from pydantic import BaseModel

from airas.types.github import GitHubConfig
from airas.types.research_history import ResearchHistory


class GithubDownloadRequest(BaseModel):
    github_config: GitHubConfig


class GithubDownloadResponse(BaseModel):
    research_history: ResearchHistory
    execution_time: dict[str, list[float]]


class GithubUploadRequest(BaseModel):
    github_config: GitHubConfig
    research_history: ResearchHistory
    commit_message: str | None = None


class GithubUploadResponse(BaseModel):
    is_github_upload: bool
    execution_time: dict[str, list[float]]
