from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class RecordVerification(BaseModel):
    ok: bool
    stage: Literal["prereg", "results"]
    problems: list[str] = Field(default_factory=list)
