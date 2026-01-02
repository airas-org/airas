from __future__ import annotations

from pydantic import BaseModel, Field


class ExperimentalAnalysis(BaseModel):
    analysis_report: str = Field(..., description="Overall analysis report text")
