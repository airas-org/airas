from pydantic import BaseModel

from airas.core.types.github import GitHubConfig


class PollGithubActionsRequestBody(BaseModel):
    github_config: GitHubConfig


class PollGithubActionsResponseBody(BaseModel):
    workflow_run_id: int | None
    status: str | None
    conclusion: str | None
    execution_time: dict[str, list[float]]


class SetGithubActionsSecretsRequestBody(BaseModel):
    github_config: GitHubConfig


class SetGithubActionsSecretsResponseBody(BaseModel):
    secrets_set: bool
    execution_time: dict[str, list[float]]
