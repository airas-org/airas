from pydantic import BaseModel

from airas.core.types.experiment_code import ExperimentCode
from airas.core.types.experimental_design import ExperimentalDesign
from airas.core.types.github import GitHubConfig
from airas.core.types.research_hypothesis import ResearchHypothesis
from airas.core.types.wandb import WandbConfig
from airas.usecases.generators.generate_code_subgraph.generate_code_subgraph import (
    GenerateCodeLLMMapping,
)


class GenerateCodeSubgraphRequestBody(BaseModel):
    research_hypothesis: ResearchHypothesis
    experimental_design: ExperimentalDesign
    wandb_config: WandbConfig
    max_code_validations: int
    llm_mapping: GenerateCodeLLMMapping | None = None


class GenerateCodeSubgraphResponseBody(BaseModel):
    experiment_code: ExperimentCode
    execution_time: dict[str, list[float]]


class PushCodeSubgraphRequestBody(BaseModel):
    github_config: GitHubConfig
    experiment_code: ExperimentCode


class PushCodeSubgraphResponseBody(BaseModel):
    code_pushed: bool
    execution_time: dict[str, list[float]]
