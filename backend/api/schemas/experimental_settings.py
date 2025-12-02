from pydantic import BaseModel

from airas.types.experimental_design import ExperimentalDesign, RunnerConfig
from airas.types.research_hypothesis import ResearchHypothesis


class GenerateExperimentalDesignSubgraphRequestBody(BaseModel):
    research_hypothesis: ResearchHypothesis
    runner_config: RunnerConfig
    num_models_to_use: int
    num_datasets_to_use: int
    num_comparative_methods: int


class GenerateExperimentalDesignSubgraphResponseBody(BaseModel):
    experimental_design: ExperimentalDesign
    execution_time: dict[str, list[float]]
