from typing import Any

from pydantic import BaseModel

from airas.core.types.github import GitHubActionsAgent, GitHubConfig  # noqa: F401
from airas.usecases.assisted_research.generate_experiment_code_subgraph.generate_experiment_code_subgraph import (
    GenerateExperimentCodeLLMMapping,
)
from airas.usecases.assisted_research.generate_verification_method_subgraph.generate_verification_method_subgraph import (
    GenerateVerificationMethodLLMMapping,
)
from airas.usecases.assisted_research.propose_verification_policy_subgraph.propose_verification_policy_subgraph import (
    ProposeVerificationPolicyLLMMapping,
)


class ProposedMethodSchema(BaseModel):
    id: str
    title: str
    what_to_verify: str
    method: str
    pros: list[str]
    cons: list[str]


class ProposePoliciesRequestBody(BaseModel):
    user_query: str
    llm_mapping: ProposeVerificationPolicyLLMMapping | None = None


class ProposePoliciesResponseBody(BaseModel):
    feasible: bool
    infeasible_reason: str | None
    proposed_methods: list[ProposedMethodSchema]


class GenerateMethodRequestBody(BaseModel):
    user_query: str
    selected_policy: ProposedMethodSchema
    llm_mapping: GenerateVerificationMethodLLMMapping | None = None


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
    llm_mapping: GenerateExperimentCodeLLMMapping | None = None


class GenerateExperimentCodeResponseBody(BaseModel):
    dispatched: bool
    workflow_run_id: int | None
    github_url: str | None
    execution_time: dict[str, list[float]]


class ExperimentCodeStatusResponseBody(BaseModel):
    status: str
    conclusion: str | None
