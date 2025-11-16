from typing_extensions import TypedDict

from airas.types.research_hypothesis import EvaluatedHypothesis
from airas.types.research_session import ResearchSession
from airas.types.research_study import ResearchStudy


class CreateHypothesisRequestBody(TypedDict):
    research_study_list: list[ResearchStudy]
    research_topic: str


class CreateHypothesisResponseBody(TypedDict):
    research_session: ResearchSession
    evaluated_hypothesis_history: list[EvaluatedHypothesis]


class CreateMethodRequestBody(TypedDict):
    research_session: ResearchSession


class CreateMethodResponseBody(TypedDict):
    research_session: ResearchSession


class CreateExperimentalDesignRequestBody(TypedDict):
    research_session: ResearchSession


class CreateExperimentalDesignResponseBody(TypedDict):
    research_session: ResearchSession


class CreateCodeRequestBody(TypedDict):
    research_session: ResearchSession


class CreateCodeResponseBody(TypedDict):
    research_session: ResearchSession
