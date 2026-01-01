from typing import Optional

from pydantic import BaseModel, Field


# https://api.semanticscholar.org/api-docs/graph#tag/Paper-Data/operation/post_graph_get_papers
class SemanticScholarInfo(BaseModel):
    title: str = Field(..., description="")
    abstract: Optional[str] = Field(None, description="")
    authors: list[str] = Field(default_factory=list, description="")

    publication_types: list[str] = Field(default_factory=list, description="")
    year: Optional[int] = Field(None, description="")
    publication_date: Optional[str] = Field(None, description="")
    venue: Optional[str] = Field(None, description="")

    journal_name: Optional[str] = Field(None, description="")
    journal_volume: Optional[str] = Field(None, description="")
    journal_pages: Optional[str] = Field(None, description="")

    external_ids: dict = Field(default_factory=dict, description="")

    citation_count: Optional[int] = Field(None, description="")
    reference_count: Optional[int] = Field(None, description="")
    influential_citation_count: Optional[int] = Field(None, description="")

    is_open_access: Optional[bool] = Field(None, description="")
    open_access_pdf_url: Optional[str] = Field(None, description="")
