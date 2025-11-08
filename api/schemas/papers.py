from pydantic import BaseModel

from airas.types.research_study import ResearchStudy


class GetPaperTitleRequestBody(BaseModel):
    queries: list[str]


class GetPaperTitleResponseBody(BaseModel):
    research_study_list: list[ResearchStudy]
