from __future__ import annotations

from pydantic import BaseModel, Field

from airas.core.types.latex import LatexBuildReport
from airas.core.types.record_verification import RecordVerification


class PaperVerification(BaseModel):
    ok: bool
    template: str
    record: RecordVerification
    problems: list[str] = Field(default_factory=list)
    # \unverified{...} claims in main.tex, surfaced for human review — they
    # are not failures, and nothing else carries them.
    unverified: list[str] = Field(default_factory=list)
    build: LatexBuildReport | None = None
    pdf: str | None = None
