from pydantic import BaseModel

from airas.types.experiment_code import ExperimentCode
from airas.types.experimental_design import ExperimentalDesign
from airas.types.research_hypothesis import ResearchHypothesis
from airas.types.wandb import WandbConfig


class GenerateCodeSubgraphRequestBody(BaseModel):
    research_hypothesis: ResearchHypothesis
    experimental_design: ExperimentalDesign
    wandb_config: WandbConfig
    max_code_validations: int


class GenerateCodeSubgraphResponseBody(BaseModel):
    experiment_code: ExperimentCode
    execution_time: dict[str, list[float]]
