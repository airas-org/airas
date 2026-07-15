from __future__ import annotations

from pydantic import BaseModel, Field


# TODO?: Output a structured analysis report instead of a plain text string.
class ExperimentalAnalysis(BaseModel):
    analysis_report: str = Field(..., description="Overall analysis report text")
