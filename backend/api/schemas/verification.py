from typing import Any

from pydantic import BaseModel

from airas.core.types.github import GitHubActionsAgent, GitHubConfig  # noqa: F401


class ProposedMethodSchema(BaseModel):
    id: str
    title: str
    what_to_verify: str
    method: str
    pros: list[str]
    cons: list[str]


class ProposePoliciesRequestBody(BaseModel):
    user_query: str


class ProposePoliciesResponseBody(BaseModel):
    feasible: bool
    infeasible_reason: str | None
    proposed_methods: list[ProposedMethodSchema]


class GenerateMethodRequestBody(BaseModel):
    user_query: str
    selected_policy: ProposedMethodSchema


class GenerateMethodResponseBody(BaseModel):
    what_to_verify: str
    experiment_settings: dict[str, dict[str, Any]]
    steps: list[str]


class GenerateExperimentCodeRequestBody(BaseModel):
    user_query: str
    what_to_verify: str
    experiment_settings: dict[str, dict[str, Any]]
    steps: list[str]
    modification_notes: str
    repository_name: str
    github_owner: str
    branch_name: str
    github_actions_agent: GitHubActionsAgent


class GenerateExperimentCodeResponseBody(BaseModel):
    dispatched: bool
    workflow_run_id: int | None
    github_url: str | None
    execution_time: dict[str, list[float]]


class ExperimentCodeStatusResponseBody(BaseModel):
    status: str
    conclusion: str | None
