from pydantic import BaseModel

from airas.types.research_hypothesis import ResearchHypothesis
from src.airas.types.research_study import ResearchStudy


class GenerateHypothesisSubgraphV0RequestBody(BaseModel):
    research_objective: str
    research_study_list: list[ResearchStudy]
    refinement_rounds: int


class GenerateHypothesisSubgraphV0ResponseBody(BaseModel):
    research_hypothesis: ResearchHypothesis
    execution_time: dict[str, list[float]]
