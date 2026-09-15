from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field


class RecordVerification(BaseModel):
    ok: bool
    stage: Literal["prereg", "results"]
    problems: list[str] = Field(default_factory=list)
    provenance: dict[str, Any] | None = Field(
        default=None,
        description=(
            "The cross-check against the backends' stored run outputs: status "
            "(verified / mismatch / unavailable) and, per results directory, "
            "the run it is pinned to, its commit, the files compared and the "
            "sibling runs of the same commit. None when it did not run."
        ),
    )
