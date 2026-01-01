from typing import Optional

from pydantic import BaseModel, Field


# https://info.arxiv.org/help/api/user-manual.html#32-the-api-response
class ArxivInfo(BaseModel):
    id: str = Field(..., description="")
    title: str = Field(..., description="")
    authors: list[str] = Field(..., description="")
    published_date: str = Field(..., description="")
    summary: str = Field(..., description="")
    journal: Optional[str] = Field(None, description="")
    doi: Optional[str] = Field(None, description="")
    affiliation: Optional[str] = Field(None, description="")
