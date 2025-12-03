from pydantic import BaseModel

from airas.types.research_hypothesis import ResearchHypothesis
from airas.types.research_study import ResearchStudy


class GenerateHypothesisSubgraphRequestBody(BaseModel):
    research_objective: str
    research_study_list: list[ResearchStudy]
    refinement_rounds: int


class GenerateHypothesisSubgraphResponseBody(BaseModel):
    research_hypothesis: ResearchHypothesis
    execution_time: dict[str, list[float]]
