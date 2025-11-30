from pydantic import BaseModel

from src.airas.types.research_study import ResearchStudy


class RetrievePaperSubgraphRequestBody(BaseModel):
    query_list: list[str]
    max_results_per_query: int


class RetrievePaperSubgraphResponseBody(BaseModel):
    research_study_list: list[list[ResearchStudy]]
    execution_time: dict[str, list[float]]
