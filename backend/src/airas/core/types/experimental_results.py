from __future__ import annotations

from typing import Any, Optional

from pydantic import BaseModel, Field


class ExperimentalResults(BaseModel):
    stdout: Optional[str] = Field(
        default=None, description="Standard output from the run"
    )
    stderr: Optional[str] = Field(
        default=None, description="Standard error from the run"
    )
    result_figures: Optional[list[str]] = Field(
        default=None, description="Result figure filenames (e.g. plot.pdf)"
    )
    diagram_figures: Optional[list[str]] = Field(
        default=None, description="Method diagram filenames (e.g. architecture.pdf)"
    )
    metrics_data: Optional[dict[str, Any]] = Field(
        default=None,
        description="Metrics data for runs (keyed by run_id or 'comparison')",
    )
