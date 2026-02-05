from datetime import datetime
from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, computed_field

from airas.core.types.experimental_design import RunnerConfig
from airas.core.types.github import GitHubConfig
from airas.core.types.research_history import ResearchHistory
from airas.core.types.wandb import WandbConfig
from airas.infra.db.models.e2e import Status, StepType
from airas.usecases.autonomous_research.topic_open_ended_research.topic_open_ended_research_subgraph import (
    TopicOpenEndedResearchSubgraphLLMMapping,
)


class TopicOpenEndedResearchRequestBody(BaseModel):
    github_config: GitHubConfig
    research_topic: str
    runner_config: RunnerConfig
    wandb_config: WandbConfig
    is_github_repo_private: bool = False
    search_method: Literal["airas_db", "qdrant"] = "airas_db"
    collection_name: str = "airas_database"
    num_paper_search_queries: int = 1
    papers_per_query: int = 2
    hypothesis_refinement_iterations: int = 1
    num_experiment_models: int = 1
    num_experiment_datasets: int = 1
    num_comparison_methods: int = 1
    experiment_code_validation_iterations: int = 3
    paper_content_refinement_iterations: int = 2
    latex_template_name: str = "mdpi"
    github_actions_agent: str = "claude_code"
    llm_mapping: TopicOpenEndedResearchSubgraphLLMMapping | None = None


class TopicOpenEndedResearchResponseBody(BaseModel):
    task_id: UUID


class TopicOpenEndedResearchStatusResponseBody(BaseModel):
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
        # Backwards compatibility for clients expecting task_id
        return self.id

    @computed_field(return_type=str | None)
    def error(self) -> str | None:
        # Backwards compatibility for clients expecting error
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


class TopicOpenEndedResearchListItemResponse(BaseModel):
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


class TopicOpenEndedResearchListResponseBody(BaseModel):
    items: list[TopicOpenEndedResearchListItemResponse]


class TopicOpenEndedResearchUpdateRequestBody(BaseModel):
    title: str | None = None
    status: Status | None = None
    current_step: StepType | None = None
    error_message: str | None = None
    result: dict[str, Any] | None = None
    github_url: str | None = None
