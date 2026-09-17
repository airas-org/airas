from dataclasses import dataclass, field
from typing import Any, Literal


@dataclass
class LiteratureMaterial:
    """A source verified outside the record, ready to be pinned into it."""

    kind: Literal["paper", "repository", "airas_record"]
    title: str
    pages: list[str]
    verified_by: str
    verified_at: str
    parser: str
    authors: list[str] = field(default_factory=list)
    year: int | None = None
    venue: str = ""
    doi: str | None = None
    arxiv_id: str | None = None
    url: str | None = None
    commit: str | None = None
    passages: list[dict[str, Any]] = field(default_factory=list)
    bib_title: str | None = None
    bib_authors: list[str] | None = None
