from pydantic import BaseModel

from airas.types.experimental_results import ExperimentalResults
from airas.types.github import GitHubConfig


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
