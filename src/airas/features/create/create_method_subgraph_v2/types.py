from typing import TypedDict

from pydantic import BaseModel


class GenerateIdea(BaseModel):
    open_problems: str
    methods: str
    experimental_setup: str
    result: str
    conclusion: str


class IdeaEvaluationResults(BaseModel):
    novelty_reason: str
    novelty_score: int
    significance_reason: str
    significance_score: int


class ResearchIdea(TypedDict):
    idea: GenerateIdea
    evaluate: IdeaEvaluationResults
