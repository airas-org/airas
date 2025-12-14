from pydantic import BaseModel

from airas.features.analyzers.analyze_experiment_subgraph.analyze_experiment_subgraph import (
    AnalyzeExperimentLLMMapping,
)
from airas.types.experiment_code import ExperimentCode
from airas.types.experimental_analysis import ExperimentalAnalysis
from airas.types.experimental_design import ExperimentalDesign
from airas.types.experimental_results import ExperimentalResults
from airas.types.github import GitHubConfig
from airas.types.research_hypothesis import ResearchHypothesis


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


class ExecuteTrialRequestBody(BaseModel):
    github_config: GitHubConfig


class ExecuteTrialResponseBody(BaseModel):
    dispatched: bool
    run_ids: list[str]
    execution_time: dict[str, list[float]]


class ExecuteFullRequestBody(BaseModel):
    github_config: GitHubConfig
    run_ids: list[str]


class ExecuteFullResponseBody(BaseModel):
    all_dispatched: bool
    branch_creation_results: list[tuple[str, str, bool]]
    execution_time: dict[str, list[float]]


class ExecuteEvaluationRequestBody(BaseModel):
    github_config: GitHubConfig


class ExecuteEvaluationResponseBody(BaseModel):
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
