from typing import Optional

from pydantic import BaseModel, Field


# TODO: ArxivInfo, SemanticScholarInfoがあればそちらに変更する
class PaperProviderSchema(BaseModel):
    title: str = Field(..., description="")
    authors: Optional[list[str]] = Field(None, description="")
    publication_year: Optional[str] = Field(None, description="")

    journal: Optional[str] = Field(None, description="")
    volume: Optional[str] = Field(None, description="")
    issue: Optional[str] = Field(None, description="")
    pages: Optional[str] = Field(None, description="")

    doi: Optional[str] = Field(None, description="")
    arxiv_id: Optional[str] = Field(None, description="")
    arxiv_url: Optional[str] = Field(None, description="")
    github_url: Optional[str] = Field(None, description="")

    abstract: Optional[str] = Field(None, description="")
