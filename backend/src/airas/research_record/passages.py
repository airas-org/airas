"""Passage identity, and the verbatim check the gate applies to a quote."""

from __future__ import annotations

import re
import unicodedata
from typing import Any

from airas.core.types.research_record import LiteratureSource, QuotedPassage
from airas.research_record.ids import next_passage_id


def _normalize(text: str) -> str:
    # Ligatures, soft hyphens and line breaks are the extractor's, not the author's.
    return " ".join(unicodedata.normalize("NFKC", text).replace("­", "").split())


def _find(fulltext: str, quote: str) -> tuple[str, int, int] | None:
    """(normalized fulltext, start, end) of the quote's first occurrence."""
    needle = _normalize(quote)
    if not needle:
        return None
    # A word the extractor broke with a hyphen at the line end ("gen-\ner-
    # alization") is matched joined as well as as written.
    for text in (fulltext, re.sub(r"-\n(?=\w)", "", fulltext)):
        hay = _normalize(text)
        if (at := hay.find(needle)) != -1:
            return hay, at, at + len(needle)
    return None


def quote_in(fulltext: str, quote: str) -> bool:
    return _find(fulltext, quote) is not None


def quote_context(fulltext: str, quote: str, margin: int = 600) -> str | None:
    """The quote with `margin` characters of its snapshot either side."""
    found = _find(fulltext, quote)
    if found is None:
        return None
    hay, start, end = found
    return hay[max(0, start - margin) : end + margin]


def add_passages(source: LiteratureSource, passages: list[dict[str, Any]]) -> None:
    for passage in passages:
        if "id" in passage:
            raise ValueError("a passage id is assigned by its source, not passed in")
        source.passages.append(
            QuotedPassage.model_validate({**passage, "id": next_passage_id(source)})
        )
