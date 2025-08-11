from typing import Any, Literal, Optional

from pydantic import BaseModel, Field


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
    acknowledgement: str = Field(..., description="")


# ExperimentalDesignを使ってまとめたい
class LLMExtractedInfo(BaseModel):
    main_contributions: str = Field(..., description="")
    methodology: str = Field(..., description="")
    experimental_setup: str = Field(..., description="")
    limitations: str = Field(..., description="")
    future_research_directions: str = Field(..., description="")
    experimental_code: Optional[str] = Field(None, description="")
    experimental_info: Optional[str] = Field(None, description="")


class MetaData(BaseModel):
    arxiv_id: Optional[str] = Field(None, description="")
    doi: Optional[str] = Field(None, description="")

    is_generated: Optional[bool] = Field(None, description="")
    authors: Optional[list[str]] = Field(None, description="")
    author_affiliations: Optional[list[str]] = Field(None, description="")
    language: Optional[str] = Field(None, description="")

    published_date: Optional[str] = Field(None, description="")
    venue: Optional[str] = Field(None, description="")
    volume: Optional[str] = Field(None, description="")
    issue: Optional[str] = Field(None, description="")
    pages: Optional[str] = Field(None, description="")

    pdf_url: Optional[str] = Field(None, description="")
    github_url: Optional[str] = Field(None, description="")

    peer_review_status: Optional[Literal["yes", "no", "unknown"]] = Field(
        None, description=""
    )
    access_type: Optional[Literal["free", "paid", "unknown"]] = Field(
        None, description=""
    )

    reference_count: Optional[int] = Field(None, description="")
    citation_count: Optional[int] = Field(None, description="")
    h_index_relevance: Optional[float] = Field(None, description="")


class AlternativeFormats(BaseModel):
    tex_data: Optional[str] = Field(None, description="")
    html_data: Optional[str] = Field(None, description="")


class ResearchStudy(BaseModel):
    title: str = Field(..., description="")
    abstract: Optional[str] = Field(None, description="")
    full_text: Optional[str] = Field(None, description="")
    image_data: Optional[Any] = Field(None, description="")
    references: Optional[dict[str, dict[str, Any]]] = Field(None, description="")
    meta_data: Optional[MetaData] = Field(None, description="")
    llm_extracted_info: Optional[LLMExtractedInfo] = Field(None, description="")
    alternative_formats: Optional[AlternativeFormats] = Field(None, description="")
