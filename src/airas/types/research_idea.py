from typing import Optional

from pydantic import BaseModel


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


class ResearchIdea(BaseModel):
    idea: GenerateIdea
    evaluate: Optional[IdeaEvaluationResults] = None
