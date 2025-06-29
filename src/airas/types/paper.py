from typing import Any, Optional

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


class LLMExtractedInfo(BaseModel):
    main_contributions: str = Field(..., description="")
    methodology: str = Field(..., description="")
    experimental_setup: str = Field(..., description="")
    limitations: str = Field(..., description="")
    future_research_directions: str = Field(..., description="")
    experimental_code: str = Field(..., description="")
    experimental_info: str = Field(..., description="")


class PaperMetaData(BaseModel):
    journal: str = Field(..., description="")
    github_url: str = Field(..., description="")


class PaperBody(BaseModel):
    title: str = Field(..., description="")
    abstract: str = Field(..., description="")
    introduction: str = Field(..., description="")
    related_work: str = Field(..., description="")
    background: str = Field(..., description="")
    method: str = Field(..., description="")
    experimental_setup: str = Field(..., description="")
    results: str = Field(..., description="")
    conclusions: str = Field(..., description="")


class PaperData(BaseModel):
    title: str = Field(..., description="")
    full_text: str = Field(..., description="")
    paper_meta_info: Optional[PaperMetaData] = Field(..., description="")
    arxiv_info: Optional[ArxivInfo] = Field(..., description="")
    llm_extracted_info: Optional[LLMExtractedInfo] = Field(..., description="")
    paper_body: Optional[PaperBody] = Field(..., description="")


class WritePaperData(BaseModel):
    paper_body: PaperBody
    citation_paper_body: PaperBody
    references: dict[str, dict[str, Any]]
    # tex_text
    tex_data: str = Field(..., description="")
    html_data: str
