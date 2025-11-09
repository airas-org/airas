from typing_extensions import TypedDict

from airas.types.research_study import ResearchStudy


class GetPaperTitleRequestBody(TypedDict):
    queries: list[str]


class GetPaperTitleResponseBody(TypedDict):
    research_study_list: list[ResearchStudy]


class RetrievePaperContentRequestBody(TypedDict):
    research_study_list: list[ResearchStudy]


class RetrievePaperContentResponseBody(TypedDict):
    research_study_list: list[ResearchStudy]


class SummarizePaperRequestBody(TypedDict):
    research_study_list: list[ResearchStudy]


class SummarizePaperResponseBody(TypedDict):
    research_study_list: list[ResearchStudy]
