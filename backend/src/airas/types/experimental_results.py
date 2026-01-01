from __future__ import annotations

from typing import Any, Optional

from pydantic import BaseModel, Field


class ExperimentalResults(BaseModel):
    stdout: Optional[str] = Field(None, description="Standard output from the run")
    stderr: Optional[str] = Field(None, description="Standard error from the run")
    figures: Optional[list[str]] = Field(
        None, description="Figures specific to this run"
    )
    metrics_data: Optional[dict[str, Any]] = Field(
        None, description="Metrics data for runs (keyed by run_id or 'comparison')"
    )
