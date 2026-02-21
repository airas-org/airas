from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

RunStage = Literal["sanity", "pilot", "main", "visualization"]


class ExperimentCode(BaseModel):
    files: dict[str, str] = Field(
        default_factory=dict,
        description="All code files keyed by relative path (e.g., 'src/train.py', 'config/run/run1.yaml')",
    )
