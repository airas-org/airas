from pydantic import BaseModel

from airas.core.types.experiment_code import ExperimentCode
from airas.core.types.experimental_design import ExperimentalDesign
from airas.core.types.github import GitHubActionsAgent, GitHubConfig
from airas.core.types.research_hypothesis import ResearchHypothesis
from airas.core.types.wandb import WandbConfig
from airas.usecases.generators.dispatch_code_generation_subgraph.dispatch_code_generation_subgraph import (
    DispatchCodeGenerationLLMMapping,
)


class DispatchCodeGenerationRequestBody(BaseModel):
    github_config: GitHubConfig
    research_topic: str
    research_hypothesis: ResearchHypothesis
    experimental_design: ExperimentalDesign
    wandb_config: WandbConfig
    github_actions_agent: GitHubActionsAgent = "open_code"
    llm_mapping: DispatchCodeGenerationLLMMapping | None = None


class DispatchCodeGenerationResponseBody(BaseModel):
    dispatched: bool
    execution_time: dict[str, list[float]]


class FetchExperimentCodeRequestBody(BaseModel):
    github_config: GitHubConfig


class FetchExperimentCodeResponseBody(BaseModel):
    experiment_code: ExperimentCode
    execution_time: dict[str, list[float]]
