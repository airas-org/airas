from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, computed_field

from airas.core.types.experimental_design import RunnerConfig
from airas.core.types.github import GitHubActionsAgent, GitHubConfig
from airas.core.types.research_history import ResearchHistory
from airas.core.types.research_hypothesis import ResearchHypothesis
from airas.core.types.research_study import ResearchStudy
from airas.core.types.wandb import WandbConfig
from airas.infra.db.models.e2e import Status, StepType
from airas.usecases.autonomous_research.topic_open_ended_research.topic_open_ended_research_subgraph_v2 import (
    TopicOpenEndedResearchSubgraphV2LLMMapping,
)


class HypothesisDrivenResearchStatusResponseBody(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    title: str
    created_by: UUID
    created_at: datetime
    status: Status
    current_step: StepType | None = None
    error_message: str | None = None
    last_updated_at: datetime
    result: dict[str, Any]
    github_url: str | None = None

    @computed_field(return_type=UUID)
    def task_id(self) -> UUID:
        return self.id

    @computed_field(return_type=str | None)
    def error(self) -> str | None:
        return self.error_message

    @computed_field(return_type=ResearchHistory | None)
    def research_history(self) -> ResearchHistory | None:
        if not self.result:
            return None
        history_data = self.result.get("research_history")
        if history_data is None:
            return None
        if isinstance(history_data, ResearchHistory):
            return history_data
        return ResearchHistory.model_validate(history_data)


class HypothesisDrivenResearchListItemResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    title: str
    created_by: UUID
    created_at: datetime
    status: Status
    current_step: StepType | None = None
    error_message: str | None = None
    last_updated_at: datetime
    github_url: str | None = None


class HypothesisDrivenResearchListResponseBody(BaseModel):
    items: list[HypothesisDrivenResearchListItemResponse]


class HypothesisDrivenResearchUpdateRequestBody(BaseModel):
    title: str | None = None
    status: Status | None = None
    current_step: StepType | None = None
    error_message: str | None = None
    result: dict[str, Any] | None = None
    github_url: str | None = None


class HypothesisDrivenResearchRequestBody(BaseModel):
    """
    Request body for hypothesis-driven research.
    Takes a research hypothesis as input instead of a research topic.
    """

    github_config: GitHubConfig
    research_hypothesis: ResearchHypothesis
    research_study_list: list[ResearchStudy] = []  # Optional: papers that informed the hypothesis
    runner_config: RunnerConfig
    wandb_config: WandbConfig
    is_github_repo_private: bool = False
    num_experiment_models: int = 1
    num_experiment_datasets: int = 1
    num_comparison_methods: int = 1
    paper_content_refinement_iterations: int = 2
    github_actions_agent: GitHubActionsAgent = "open_code"
    latex_template_name: str = "mdpi"
    llm_mapping: TopicOpenEndedResearchSubgraphV2LLMMapping | None = None


class HypothesisDrivenResearchResponseBody(BaseModel):
    task_id: UUID
