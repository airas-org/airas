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
        default=None,
        description=(
            "Result figure paths relative to the results directory, which is "
            "also their path under the paper's images/ (e.g. run-1/plot.pdf "
            "is referenced as images/run-1/plot.pdf)"
        ),
    )
    diagram_figures: Optional[list[str]] = Field(
        default=None,
        description=(
            "Method diagram paths, relative in the same way as result_figures "
            "(e.g. diagram/architecture.pdf)"
        ),
    )
    metrics_data: Optional[dict[str, Any]] = Field(
        default=None,
        description="Metrics data for runs (keyed by run_id or 'comparison')",
    )
