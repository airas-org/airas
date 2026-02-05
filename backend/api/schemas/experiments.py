from pydantic import BaseModel

from airas.core.types.experiment_code import ExperimentCode
from airas.core.types.experimental_analysis import ExperimentalAnalysis
from airas.core.types.experimental_design import ExperimentalDesign
from airas.core.types.experimental_results import ExperimentalResults
from airas.core.types.github import GitHubActionsAgent, GitHubConfig
from airas.core.types.research_hypothesis import ResearchHypothesis
from airas.usecases.analyzers.analyze_experiment_subgraph.analyze_experiment_subgraph import (
    AnalyzeExperimentLLMMapping,
)
from airas.usecases.executors.execute_evaluation_subgraph.execute_evaluation_subgraph import (
    ExecuteEvaluationLLMMapping,
)
from airas.usecases.executors.execute_full_experiment_subgraph.execute_full_experiment_subgraph import (
    ExecuteFullExperimentLLMMapping,
)
from airas.usecases.executors.execute_trial_experiment_subgraph.execute_trial_experiment_subgraph import (
    ExecuteTrialExperimentLLMMapping,
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


class ExecuteTrialRequestBody(BaseModel):
    github_config: GitHubConfig
    github_actions_agent: GitHubActionsAgent = "claude_code"
    llm_mapping: ExecuteTrialExperimentLLMMapping | None = None


class ExecuteTrialResponseBody(BaseModel):
    dispatched: bool
    run_ids: list[str]
    execution_time: dict[str, list[float]]


class ExecuteFullRequestBody(BaseModel):
    github_config: GitHubConfig
    run_ids: list[str]
    github_actions_agent: GitHubActionsAgent = "claude_code"
    llm_mapping: ExecuteFullExperimentLLMMapping | None = None


class ExecuteFullResponseBody(BaseModel):
    all_dispatched: bool
    branch_creation_results: list[tuple[str, str, bool]]
    execution_time: dict[str, list[float]]


class ExecuteEvaluationRequestBody(BaseModel):
    github_config: GitHubConfig
    github_actions_agent: GitHubActionsAgent = "claude_code"
    llm_mapping: ExecuteEvaluationLLMMapping | None = None


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
