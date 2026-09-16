"""Passage identity, and the verbatim check the gate applies to a quote."""

from __future__ import annotations

import unicodedata
from typing import Any

from airas.core.types.research_record import LiteratureSource, QuotedPassage
from airas.research_record.ids import next_passage_id


def _normalize(text: str) -> str:
    # Ligatures, soft hyphens and line breaks are the extractor's, not the author's.
    return " ".join(unicodedata.normalize("NFKC", text).replace("­", "").split())


def quote_in(fulltext: str, quote: str) -> bool:
    needle = _normalize(quote)
    return bool(needle) and needle in _normalize(fulltext)


def add_passages(source: LiteratureSource, passages: list[dict[str, Any]]) -> None:
    for passage in passages:
        if "id" in passage:
            raise ValueError("a passage id is assigned by its source, not passed in")
        source.passages.append(
            QuotedPassage.model_validate({**passage, "id": next_passage_id(source)})
        )
