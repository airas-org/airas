from pydantic import BaseModel

from airas.types.github import GitHubConfig


class PollGithubActionsRequestBody(BaseModel):
    github_config: GitHubConfig


class PollGithubActionsResponseBody(BaseModel):
    workflow_run_id: int | None
    status: str | None
    conclusion: str | None
    execution_time: dict[str, list[float]]
