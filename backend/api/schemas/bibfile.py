from pydantic import BaseModel

from airas.core.types.research_study import ResearchStudy


class GenerateBibfileSubgraphRequestBody(BaseModel):
    research_study_list: list[ResearchStudy]


class GenerateBibfileSubgraphResponseBody(BaseModel):
    references_bib: str
    execution_time: dict[str, list[float]]
