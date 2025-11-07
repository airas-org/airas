from pydantic import BaseModel

from airas.types.research_study import ResearchStudy


class GetPaperTitleRequest(BaseModel):
    queries: list[str]


class GetPaperTitleResponse(BaseModel):
    research_study_list: list[ResearchStudy]
