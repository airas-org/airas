from typing import Optional

from pydantic import BaseModel, Field


class SemanticScholarInfo(BaseModel):
    title: str = Field(..., description="")
    abstract: Optional[str] = Field(None, description="")
    authors: list[str] = Field(default_factory=list, description="")

    publication_types: list[str] = Field(default_factory=list, description="")
    publication_year: Optional[int] = Field(None, description="")
    publication_date: Optional[str] = Field(None, description="")
    journal: Optional[str] = Field(None, description="")

    volume: Optional[str] = Field(None, description="")
    issue: Optional[str] = Field(None, description="")
    pages: Optional[str] = Field(None, description="")

    doi: Optional[str] = Field(None, description="")
    arxiv_id: Optional[str] = Field(None, description="")
    arxiv_url: Optional[str] = Field(None, description="")
