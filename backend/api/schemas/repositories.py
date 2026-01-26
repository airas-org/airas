from pydantic import BaseModel

from airas.core.types.github import GitHubConfig


class PrepareRepositorySubgraphRequestBody(BaseModel):
    github_config: GitHubConfig
    is_private: bool


class PrepareRepositorySubgraphResponseBody(BaseModel):
    is_repository_ready: bool
    is_branch_ready: bool
    execution_time: dict[str, list[float]]
