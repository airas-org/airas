from __future__ import annotations

import json
from typing import Literal, Optional

from pydantic import BaseModel, Field


class LLMExtractedInfo(BaseModel):
    main_contributions: Optional[str] = Field(None, description="")
    methodology: Optional[str] = Field(None, description="")
    experimental_setup: Optional[str] = Field(None, description="")
    limitations: Optional[str] = Field(None, description="")
    future_research_directions: Optional[str] = Field(None, description="")
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


class ResearchStudy(BaseModel):
    title: str = Field(..., description="")
    full_text: str = Field(..., description="")
    references: list[str] = Field(
        ..., description=""
    )  # TODO: Consider how much information to obtain from the cited papers.
    meta_data: MetaData = Field(..., description="")
    llm_extracted_info: LLMExtractedInfo

    def to_formatted_json(self) -> str:
        data_dict = {
            "Title": self.title,
            "Main Contributions": self.llm_extracted_info.main_contributions,
            "Methods": self.llm_extracted_info.methodology,
            "Experimental Setup": self.llm_extracted_info.experimental_setup,
            "Limitations": self.llm_extracted_info.limitations,
            "Future Research Directions": self.llm_extracted_info.future_research_directions,
            "Experimental Code": self.llm_extracted_info.experimental_code,
            "Experimental Info": self.llm_extracted_info.experimental_info,
        }
        return json.dumps(data_dict, ensure_ascii=False, indent=4)
