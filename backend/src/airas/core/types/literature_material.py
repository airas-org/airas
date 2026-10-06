from dataclasses import dataclass, field
from typing import Any


@dataclass
class RepositoryMaterial:
    """Code at a commit, snapshotted as one page per file."""

    url: str
    commit: str
    pages: list[str]
    method_entry: str = ""


@dataclass
class LiteratureMaterial:
    """A source verified outside the record, ready to be pinned into it."""

    title: str
    verified_by: str
    verified_at: str
    parser: str
    pages: list[str] = field(default_factory=list)
    authors: list[str] = field(default_factory=list)
    year: int | None = None
    venue: str = ""
    doi: str | None = None
    arxiv_id: str | None = None
    url: str | None = None
    repositories: list[RepositoryMaterial] = field(default_factory=list)
    passages: list[dict[str, Any]] = field(default_factory=list)
    bib_title: str | None = None
    bib_authors: list[str] | None = None
