from pydantic import BaseModel

from airas.core.types.github import GitHubActionsAgent
from airas.dashboard.api.schemas.github import GitHubConfigRequest
from airas.usecases.executors.fetch_paper_reproduction_results_subgraph.fetch_paper_reproduction_results_subgraph import (
    FetchPaperReproductionResultsLLMMapping,
)
from airas.usecases.generators.dispatch_paper_reproduction_generate_subgraph.dispatch_paper_reproduction_generate_subgraph import (
    DispatchPaperReproductionGenerateLLMMapping,
)


class DispatchPaperReproductionGenerateRequestBody(BaseModel):
    github_config: GitHubConfigRequest
    paper_url: str
    instruction: str
    repo_url: str = ""
    github_actions_agent: GitHubActionsAgent = "claude_code"
    runner_label: list[str] | None = None
    llm_mapping: DispatchPaperReproductionGenerateLLMMapping | None = None


class DispatchPaperReproductionGenerateResponseBody(BaseModel):
    dispatched: bool
    repro_id: str
    execution_time: dict[str, list[float]]


class DispatchPaperReproductionRunRequestBody(BaseModel):
    github_config: GitHubConfigRequest
    repro_id: str
    repo_url: str = ""
    runner_label: list[str] | None = None


class DispatchPaperReproductionRunResponseBody(BaseModel):
    dispatched: bool
    execution_time: dict[str, list[float]]


class FetchPaperReproductionResultsRequestBody(BaseModel):
    github_config: GitHubConfigRequest
    repro_id: str
    llm_mapping: FetchPaperReproductionResultsLLMMapping | None = None


class FetchPaperReproductionResultsResponseBody(BaseModel):
    result: dict | None
    validation: dict | None
    final_status: dict | None
    repro_md: str | None
    repro_png_base64: str | None
    execution_time: dict[str, list[float]]


class DispatchParameterTuningRunRequestBody(BaseModel):
    github_config: GitHubConfigRequest
    repro_id: str
    repo_url: str = ""
    runner_label: list[str] | None = None


class DispatchParameterTuningRunResponseBody(BaseModel):
    dispatched: bool
    execution_time: dict[str, list[float]]


class FetchParameterTuningResultsRequestBody(BaseModel):
    github_config: GitHubConfigRequest
    repro_id: str


class FetchParameterTuningResultsResponseBody(BaseModel):
    result: dict | None
    tuning_figure_png_base64: str | None
    final_status: dict | None
    execution_time: dict[str, list[float]]
