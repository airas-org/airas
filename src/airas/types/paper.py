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


class LLMExtractedInfo(BaseModel):
    main_contributions: str = Field(..., description="")
    methodology: str = Field(..., description="")
    experimental_setup: str = Field(..., description="")
    limitations: str = Field(..., description="")
    future_research_directions: str = Field(..., description="")
    experimental_code: Optional[str] = Field(None, description="")
    experimental_info: Optional[str] = Field(None, description="")


class MetaData(BaseModel):
    peer_review_status: Optional[Literal["yes", "no", "unknown"]] = Field(
        None, description=""
    )
    language: Optional[str] = Field(None, description="")
    access_type: Optional[Literal["free", "paid", "unknown"]] = Field(
        None, description=""
    )
    journal: Optional[str] = Field(None, description="")
    github_url: Optional[str] = Field(None, description="")
    authors: Optional[list[str]] = Field(None, description="")
    is_generated: Optional[bool] = Field(None, description="")


class AlternativeFormats(BaseModel):
    tex_data: Optional[str] = Field(None, description="")
    html_data: Optional[str] = Field(None, description="")


class ExternalSources(BaseModel):
    arxiv_info: Optional[ArxivInfo] = Field(None, description="")
    # openalex_info: OpenAlexInfo


class PaperData(BaseModel):
    title: str = Field(..., description="")
    full_text: Optional[str] = Field(None, description="")
    paper_body: Optional[PaperBody] = Field(None, description="")
    image_data: Optional[Any] = Field(None, description="")
    citation_paper_body: Optional[PaperBody] = Field(None, description="")
    references: Optional[dict[str, dict[str, Any]]] = Field(None, description="")
    # TODO:引用論文の取得ロジックを変更し以下に変更する
    # references: Optional[list[PaperBody]] = Field(None, description="")
    meta_data: Optional[MetaData] = Field(None, description="")
    external_sources: Optional[ExternalSources] = Field(None, description="")
    llm_extracted_info: Optional[LLMExtractedInfo] = Field(None, description="")
    alternative_formats: Optional[AlternativeFormats] = Field(None, description="")
