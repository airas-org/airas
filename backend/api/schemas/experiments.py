from pydantic import BaseModel

from airas.core.types.experiment_code import ExperimentCode, RunStage
from airas.core.types.experimental_analysis import ExperimentalAnalysis
from airas.core.types.experimental_design import ExperimentalDesign
from airas.core.types.experimental_results import ExperimentalResults
from airas.core.types.github import GitHubActionsAgent, GitHubConfig
from airas.core.types.research_hypothesis import ResearchHypothesis
from airas.core.types.wandb import WandbConfig
from airas.usecases.analyzers.analyze_experiment_subgraph.analyze_experiment_subgraph import (
    AnalyzeExperimentLLMMapping,
)
from airas.usecases.executors.dispatch_experiment_validation_subgraph.dispatch_experiment_validation_subgraph import (
    DispatchExperimentValidationLLMMapping,
)


class FetchRunIdsRequestBody(BaseModel):
    github_config: GitHubConfig


class FetchRunIdsResponseBody(BaseModel):
    run_ids: list[str]
    execution_time: dict[str, list[float]]


class FetchExperimentalResultsRequestBody(BaseModel):
    github_config: GitHubConfig


class FetchExperimentalResultsResponseBody(BaseModel):
    experiment_results: ExperimentalResults
    execution_time: dict[str, list[float]]


class DispatchSanityCheckRequestBody(BaseModel):
    github_config: GitHubConfig
    run_id: str


class DispatchSanityCheckResponseBody(BaseModel):
    dispatched: bool
    execution_time: dict[str, list[float]]


class DispatchMainExperimentRequestBody(BaseModel):
    github_config: GitHubConfig
    run_id: str


class DispatchMainExperimentResponseBody(BaseModel):
    dispatched: bool
    execution_time: dict[str, list[float]]


class DispatchVisualizationRequestBody(BaseModel):
    github_config: GitHubConfig
    run_ids: list[str]


class DispatchVisualizationResponseBody(BaseModel):
    dispatched: bool
    execution_time: dict[str, list[float]]


class DispatchExperimentValidationRequestBody(BaseModel):
    github_config: GitHubConfig
    research_topic: str
    run_id: str
    workflow_run_id: int
    run_stage: RunStage
    research_hypothesis: ResearchHypothesis
    experimental_design: ExperimentalDesign
    wandb_config: WandbConfig
    github_actions_agent: GitHubActionsAgent = "open_code"
    llm_mapping: DispatchExperimentValidationLLMMapping | None = None


class DispatchExperimentValidationResponseBody(BaseModel):
    dispatched: bool
    execution_time: dict[str, list[float]]


class AnalyzeExperimentRequestBody(BaseModel):
    research_hypothesis: ResearchHypothesis
    experimental_design: ExperimentalDesign
    experiment_code: ExperimentCode
    experimental_results: ExperimentalResults
    llm_mapping: AnalyzeExperimentLLMMapping | None = None


class AnalyzeExperimentResponseBody(BaseModel):
    experimental_analysis: ExperimentalAnalysis
    execution_time: dict[str, list[float]]
