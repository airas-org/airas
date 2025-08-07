from typing import Optional

from pydantic import BaseModel, Field


class ArxivInfo(BaseModel):
    id: str = Field(..., description="")
    url: str = Field(..., description="")
    title: str = Field(..., description="")
    authors: list[str] = Field(..., description="")
    published_date: str = Field(..., description="")
    summary: str = Field(..., description="")
    journal: Optional[str] = Field(None, description="")
    doi: Optional[str] = Field(None, description="")
    affiliation: Optional[str] = Field(None, description="")
