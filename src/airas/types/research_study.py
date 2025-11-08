from __future__ import annotations

import json
from typing import Any, Literal, Optional

from pydantic import BaseModel, Field


# ExperimentalDesignを使ってまとめたい
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
    abstract: Optional[str] = Field(None, description="")
    full_text: Optional[str] = Field(None, description="")
    image_data: Optional[Any] = Field(None, description="")
    references: Optional[dict[str, dict[str, Any]]] = Field(None, description="")
    meta_data: Optional[MetaData] = Field(None, description="")
    llm_extracted_info: Optional[LLMExtractedInfo] = Field(None, description="")

    def to_formatted_dict(self) -> dict[str, Any]:
        if not (info := self.llm_extracted_info):
            return {}
        return {
            "Title": self.title,
            "Main Contributions": info.main_contributions,
            "Methodology": info.methodology,
            "Experimental Setup": info.experimental_setup,
            "Limitations": info.limitations,
            "Future Research Directions": info.future_research_directions,
            "Experiment Code": info.experimental_code,
            "Experiment Result": info.experimental_info,
        }

    @classmethod
    def format_list(cls, research_study_list: list[ResearchStudy]) -> str:
        return "".join(
            json.dumps(data_dict, ensure_ascii=False, indent=4)
            for research_study in research_study_list
            if (data_dict := research_study.to_formatted_dict())
        )
