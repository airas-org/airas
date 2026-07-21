import re
from typing import Annotated

from pydantic import AfterValidator, BaseModel

from airas.core.types.github import GitHubActionsAgent
from airas.dashboard.api.schemas.github import GitHubConfigRequest
from airas.usecases.executors.fetch_paper_reproduction_results_subgraph.fetch_paper_reproduction_results_subgraph import (
    FetchPaperReproductionResultsLLMMapping,
)
from airas.usecases.generators.dispatch_paper_reproduction_generate_subgraph.dispatch_paper_reproduction_generate_subgraph import (
    DispatchPaperReproductionGenerateLLMMapping,
)

# repro_id is interpolated into a GitHub Actions workflow_dispatch input (e.g.
# `.reproduction/${{ inputs.repro_id }}`) and, on the fetch side, a GitHub Contents API path
# segment. Restrict it to generate_repro_id's own output charset and reject "."/".." outright so a
# crafted value can't escape the .reproduction/<repro_id>/ directory.
_REPRO_ID_RE = re.compile(r"^[A-Za-z0-9._-]+$")


def _validate_repro_id(value: str) -> str:
    if value in (".", "..") or not _REPRO_ID_RE.fullmatch(value):
        raise ValueError(f"invalid repro_id: {value!r}")
    return value


ReproId = Annotated[str, AfterValidator(_validate_repro_id)]


class DispatchPaperReproductionGenerateRequestBody(BaseModel):
    github_config: GitHubConfigRequest
    paper_url: str
    instruction: str
    repo_url: str = ""
    github_actions_agent: GitHubActionsAgent = "claude_code"
    runner_label: list[str] | None = None
    llm_mapping: DispatchPaperReproductionGenerateLLMMapping


class DispatchPaperReproductionGenerateResponseBody(BaseModel):
    dispatched: bool
    repro_id: str
    execution_time: dict[str, list[float]]


class DispatchPaperReproductionRunRequestBody(BaseModel):
    github_config: GitHubConfigRequest
    repro_id: ReproId
    repo_url: str = ""
    runner_label: list[str] | None = None


class DispatchPaperReproductionRunResponseBody(BaseModel):
    dispatched: bool
    execution_time: dict[str, list[float]]


class FetchPaperReproductionResultsRequestBody(BaseModel):
    github_config: GitHubConfigRequest
    repro_id: ReproId
    llm_mapping: FetchPaperReproductionResultsLLMMapping


class FetchPaperReproductionResultsResponseBody(BaseModel):
    result: dict | None
    validation: dict | None
    final_status: dict | None
    repro_md: str | None
    repro_png_base64: str | None
    execution_time: dict[str, list[float]]


class DispatchParameterTuningRunRequestBody(BaseModel):
    github_config: GitHubConfigRequest
    repro_id: ReproId
    repo_url: str = ""
    runner_label: list[str] | None = None


class DispatchParameterTuningRunResponseBody(BaseModel):
    dispatched: bool
    execution_time: dict[str, list[float]]


class FetchParameterTuningResultsRequestBody(BaseModel):
    github_config: GitHubConfigRequest
    repro_id: ReproId


class FetchParameterTuningResultsResponseBody(BaseModel):
    result: dict | None
    tuning_figure_png_base64: str | None
    final_status: dict | None
    execution_time: dict[str, list[float]]
