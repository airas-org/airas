from pydantic import BaseModel

from airas.types.github import GitHubConfig


class PollWorkflowRequestBody(BaseModel):
    github_config: GitHubConfig


class PollWorkflowResponseBody(BaseModel):
    workflow_run_id: int | None
    status: str | None
    conclusion: str | None
    execution_time: dict[str, list[float]]
