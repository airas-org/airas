from pydantic import BaseModel, SecretStr

from airas.core.types.github import GitHubActionsAgent, GitHubConfig


class DispatchInteractiveRepoAgentRequestBody(BaseModel):
    github_config: GitHubConfig
    github_actions_agent: GitHubActionsAgent
    session_username: str
    session_password: SecretStr


class DispatchInteractiveRepoAgentResponseBody(BaseModel):
    dispatched: bool
    workflow_run_id: int | None
    tunnel_url: str | None
    execution_time: dict[str, list[float]]


class CancelInteractiveRepoAgentRequestBody(BaseModel):
    github_config: GitHubConfig


class CancelInteractiveRepoAgentResponseBody(BaseModel):
    cancelled: bool
    execution_time: dict[str, list[float]]
