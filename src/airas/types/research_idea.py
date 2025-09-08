from pydantic import BaseModel
from typing_extensions import TypedDict


class GenerateIdea(BaseModel):
    open_problems: str
    methods: str
    experimental_setup: str
    expected_result: str
    expected_conclusion: str


class IdeaEvaluationResults(BaseModel):
    novelty_reason: str
    novelty_score: int
    significance_reason: str
    significance_score: int


class ResearchIdea(TypedDict):
    idea: GenerateIdea
    evaluate: IdeaEvaluationResults
