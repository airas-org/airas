from uuid import UUID

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
    pros: list[str] = []
    cons: list[str] = []


class ProposePoliciesRequestBody(BaseModel):
    user_query: str
    llm_mapping: ProposeVerificationPolicyLLMMapping | None = None
    verification_id: UUID | None = None


class ProposePoliciesResponseBody(BaseModel):
    feasible: bool
    infeasible_reason: str | None
    proposed_methods: list[ProposedMethodSchema]
    execution_time: dict[str, list[float]]


class GenerateMethodRequestBody(BaseModel):
    user_query: str
    selected_policy: ProposedMethodSchema
    llm_mapping: GenerateVerificationMethodLLMMapping | None = None
    verification_id: UUID | None = None


class GenerateMethodResponseBody(BaseModel):
    what_to_verify: str
    experiment_settings: dict[str, str]
    steps: list[str]
    execution_time: dict[str, list[float]]


class GenerateExperimentCodeRequestBody(BaseModel):
    user_query: str
    what_to_verify: str
    experiment_settings: dict[str, str]
    steps: list[str]
    modification_notes: str
    repository_name: str
    github_owner: str
    branch_name: str
    github_actions_agent: GitHubActionsAgent
    llm_mapping: GenerateExperimentCodeLLMMapping | None = None
    verification_id: UUID | None = None


class GenerateExperimentCodeResponseBody(BaseModel):
    dispatched: bool
    workflow_run_id: int | None
    github_url: str | None
    execution_time: dict[str, list[float]]


class ExperimentCodeStatusResponseBody(BaseModel):
    status: str
    conclusion: str | None


class VerificationSessionResponse(BaseModel):
    id: str
    title: str
    query: str
    created_by: str
    created_at: str
    updated_at: str
    phase: str
    proposed_methods: list[ProposedMethodSchema] | None = None
    selected_method_id: str | None = None
    verification_method: dict | None = None
    plan: dict | None = None
    repository_name: str | None = None
    github_owner: str | None = None
    github_url: str | None = None
    workflow_run_id: int | None = None
    modification_notes: str | None = None
    code_generation_status: str | None = None
    code_generation_conclusion: str | None = None
    implementation: dict | None = None
    paper_draft: dict | None = None


class VerificationSessionCreateRequest(BaseModel):
    title: str = "名称未設定"


class VerificationSessionUpdateRequest(BaseModel):
    title: str | None = None
    query: str | None = None
    phase: str | None = None
    proposed_methods: list[ProposedMethodSchema] | None = None
    selected_method_id: str | None = None
    verification_method: dict | None = None
    plan: dict | None = None
    repository_name: str | None = None
    github_owner: str | None = None
    github_url: str | None = None
    workflow_run_id: int | None = None
    modification_notes: str | None = None
    code_generation_status: str | None = None
    code_generation_conclusion: str | None = None
    implementation: dict | None = None
    paper_draft: dict | None = None


class VerificationSessionListResponse(BaseModel):
    sessions: list[VerificationSessionResponse]
