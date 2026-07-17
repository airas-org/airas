from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field

# Sources supported by the multi-source paper search.
PAPER_SEARCH_SOURCES = ("openalex", "semantic_scholar", "arxiv", "airas_db")


class PaperSearchResult(BaseModel):
    """A paper found by any search source, normalized to a common shape."""

    title: str
    authors: list[str] = Field(default_factory=list)
    abstract: Optional[str] = None
    doi: Optional[str] = None
    arxiv_id: Optional[str] = None
    url: Optional[str] = None
    pdf_url: Optional[str] = None
    published_date: Optional[str] = None
    venue: Optional[str] = None
    citations: Optional[int] = None
    # Which search source this result came from (see PAPER_SEARCH_SOURCES).
    source: str
    # Source-native identifiers, e.g. {"openalex": "W123", "semantic_scholar": "abc"}.
    external_ids: dict[str, str] = Field(default_factory=dict)
