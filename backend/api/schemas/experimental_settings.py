from pydantic import BaseModel

from airas.core.types.experiment_history import ExperimentHistory
from airas.core.types.experimental_design import ComputeEnvironment, ExperimentalDesign
from airas.core.types.research_hypothesis import ResearchHypothesis
from airas.usecases.generators.generate_experimental_design_subgraph.generate_experimental_design_subgraph import (
    GenerateExperimentalDesignLLMMapping,
)
from airas.usecases.generators.refine_experimental_design_subgraph.refine_experimental_design_subgraph import (
    RefineExperimentalDesignLLMMapping,
)


class GenerateExperimentalDesignSubgraphRequestBody(BaseModel):
    research_hypothesis: ResearchHypothesis
    compute_environment: ComputeEnvironment
    num_models_to_use: int
    num_datasets_to_use: int
    num_comparative_methods: int
    llm_mapping: GenerateExperimentalDesignLLMMapping | None = None


class GenerateExperimentalDesignSubgraphResponseBody(BaseModel):
    experimental_design: ExperimentalDesign
    execution_time: dict[str, list[float]]


class RefineExperimentalDesignSubgraphRequestBody(BaseModel):
    research_hypothesis: ResearchHypothesis
    experiment_history: ExperimentHistory
    design_instruction: str
    compute_environment: ComputeEnvironment
    num_models_to_use: int
    num_datasets_to_use: int
    num_comparative_methods: int
    llm_mapping: RefineExperimentalDesignLLMMapping | None = None


class RefineExperimentalDesignSubgraphResponseBody(BaseModel):
    experimental_design: ExperimentalDesign
    execution_time: dict[str, list[float]]
