from pydantic import BaseModel

from airas.core.types.experimental_design import ExperimentalDesign, RunnerConfig
from airas.core.types.research_hypothesis import ResearchHypothesis
from airas.usecases.generators.generate_experimental_design_subgraph.generate_experimental_design_subgraph import (
    GenerateExperimentalDesignLLMMapping,
)


class GenerateExperimentalDesignSubgraphRequestBody(BaseModel):
    research_hypothesis: ResearchHypothesis
    runner_config: RunnerConfig
    num_models_to_use: int
    num_datasets_to_use: int
    num_comparative_methods: int
    llm_mapping: GenerateExperimentalDesignLLMMapping | None = None


class GenerateExperimentalDesignSubgraphResponseBody(BaseModel):
    experimental_design: ExperimentalDesign
    execution_time: dict[str, list[float]]
