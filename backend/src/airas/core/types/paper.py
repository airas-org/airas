from typing import Optional, TypeAlias, Union

from pydantic import BaseModel, Field
from typing_extensions import TypedDict


class CandidatePaperInfo(TypedDict):
    arxiv_id: str
    arxiv_url: str
    title: str
    authors: list[str]
    published_date: str
    journal: str
    doi: str
    summary: str
    github_url: str
    main_contributions: str
    methodology: str
    experimental_setup: str
    limitations: str
    future_research_directions: str


# TODO: Move to ResearchStudy or ResearchHypothesis
class PaperReviewScores(BaseModel):
    novelty_score: Optional[int] = Field(None, description="Paper novelty score")
    significance_score: Optional[int] = Field(
        None, description="Paper significance score"
    )
    reproducibility_score: Optional[int] = Field(
        None, description="Paper reproducibility score"
    )
    experimental_quality_score: Optional[int] = Field(
        None, description="Paper experimental quality score"
    )


class BasePaperContent(BaseModel):
    title: str = Field(min_length=1)
    abstract: str = Field(min_length=1)
    introduction: str = Field(min_length=1)
    related_work: str = Field(min_length=1)
    background: str = Field(min_length=1)
    method: str = Field(min_length=1)
    experimental_setup: str = Field(min_length=1)
    results: str = Field(min_length=1)
    conclusion: str = Field(min_length=1)


class ICLR2024PaperContent(BasePaperContent):
    pass


PaperContent: TypeAlias = BasePaperContent
# TODO: Extend PaperContent alias to a Union with additional template-specific models.
