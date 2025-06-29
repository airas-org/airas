from typing import Any, Literal, Optional

from pydantic import BaseModel, Field
from typing_extensions import TypedDict

from airas.types.arxiv import ArxivInfo


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


class PaperContent(BaseModel):
    Title: str
    Abstract: str
    Introduction: str
    Related_Work: str
    Background: str
    Method: str
    Experimental_Setup: str
    Results: str
    Conclusions: str


class PaperBody(BaseModel):
    title: str = Field(..., description="")
    abstract: str
    introduction: str
    related_work: str
    background: str
    method: str
    experimental_setup: str
    results: str
    conclusions: str
    acknowledgement: str
    image_data: Any = Field(..., description="")


class LLMExtractedInfo(BaseModel):
    main_contributions: str = Field(..., description="")
    methodology: str = Field(..., description="")
    experimental_setup: str = Field(..., description="")
    limitations: str = Field(..., description="")
    future_research_directions: str = Field(..., description="")
    github_code: str = Field(..., description="")


class MetaData(BaseModel):
    peer_review_status: Literal["yes", "no", "unknown"]
    language: str
    access_type: Literal["free", "paid", "unknown"]
    journal: str
    github_url: str
    authors: list[str]
    is_generated: bool


class AlternativeFormats(BaseModel):
    tex_data: str
    html_data: str


class ExternalSources(BaseModel):
    arxiv_info: ArxivInfo
    # openalex_info: OpenAlexInfo


class PaperData(BaseModel):
    title: str = Field(..., description="")
    full_text: Optional[str] = Field(..., description="")
    paper_body: Optional[PaperBody] = Field(..., description="")
    # ？citation_paper_body: PaperBody
    references: Optional[list[PaperBody]] = Field(..., description="")
    meta_data: Optional[MetaData] = Field(..., description="")
    external_sources: Optional[ExternalSources] = Field(..., description="")
    llm_extracted_info: Optional[LLMExtractedInfo] = Field(..., description="")
    alternative_formats: Optional[AlternativeFormats] = Field(..., description="")
