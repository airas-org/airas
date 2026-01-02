from pydantic import BaseModel

from airas.features.generators.generate_hypothesis_subgraph.generate_hypothesis_subgraph_v0 import (
    GenerateHypothesisSubgraphV0LLMMapping,
)
from airas.types.research_hypothesis import ResearchHypothesis
from airas.types.research_study import ResearchStudy


class GenerateHypothesisSubgraphV0RequestBody(BaseModel):
    research_topic: str
    research_study_list: list[ResearchStudy]
    refinement_rounds: int
    llm_mapping: GenerateHypothesisSubgraphV0LLMMapping | None = None


class GenerateHypothesisSubgraphV0ResponseBody(BaseModel):
    research_hypothesis: ResearchHypothesis
    execution_time: dict[str, list[float]]
