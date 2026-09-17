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
    # Registered sources main.tex never cites: read and set aside, or
    # forgotten — for the author to say, not a failure.
    uncited_sources: list[str] = Field(default_factory=list)
    # What the record's citation judgments say of the paper as it stands.
    # A citation no judgment covers is also a problem; one judged unsupported
    # is review input like the two above.
    unjudged_citations: list[str] = Field(default_factory=list)
    unsupported_citations: list[str] = Field(default_factory=list)
    build: LatexBuildReport | None = None
    pdf: str | None = None
