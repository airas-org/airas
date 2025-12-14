from pydantic import BaseModel

from airas.features.generators.generate_experimental_design_subgraph.generate_experimental_design_subgraph import (
    GenerateExperimentalDesignLLMMapping,
)
from airas.types.experimental_design import ExperimentalDesign, RunnerConfig
from airas.types.research_hypothesis import ResearchHypothesis


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
