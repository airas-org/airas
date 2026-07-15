from __future__ import annotations

from pydantic import BaseModel, Field


class ExperimentCode(BaseModel):
    files: dict[str, str] = Field(
        default_factory=dict,
        description="All code files keyed by relative path (e.g., 'src/train.py', 'config/run/run1.yaml')",
    )
