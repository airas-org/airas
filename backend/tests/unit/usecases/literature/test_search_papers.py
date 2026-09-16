"""Sources run side by side; one failing is reported, and duplicates across
sources become one row."""

import asyncio

import pytest

from airas.core.types.paper_search import PaperSearchResult
from airas.usecases.literature.search_papers import (
    SourceOutput,
    merge_results,
    parse_sources,
    run_source,
)


def _paper(source: str, **fields: object) -> PaperSearchResult:
    return PaperSearchResult(title="Attention Is All You Need", source=source, **fields)


def test_duplicates_merge_in_source_order_and_fill_each_other() -> None:
    result = merge_results(
        {
            "arxiv": SourceOutput(
                papers=[
                    _paper("arxiv", arxiv_id="1706.03762", pdf_url="https://x/pdf")
                ],
                error=None,
            ),
            "openalex": SourceOutput(
                papers=[_paper("openalex", doi="10.1/a", citations=9)], error=None
            ),
            "semantic_scholar": SourceOutput(papers=[], error="rate limited"),
        }
    )
    (kept,) = result["papers"]
    assert kept.source == "openalex"  # first in source order wins
    assert (kept.doi, kept.arxiv_id, kept.pdf_url, kept.citations) == (
        "10.1/a",
        "1706.03762",
        "https://x/pdf",
        9,
    )
    assert result["source_results"] == {
        "openalex": 1,
        "semantic_scholar": 0,
        "arxiv": 1,
    }
    assert result["search_errors"] == {"semantic_scholar": "rate limited"}


def test_a_source_that_raises_is_reported_not_raised() -> None:
    async def boom() -> list[PaperSearchResult]:
        raise RuntimeError("down")

    assert asyncio.run(run_source("arxiv", boom)) == (
        "arxiv",
        SourceOutput(papers=[], error="down"),
    )


def test_sources_are_parsed_and_unknown_ones_refused() -> None:
    assert parse_sources("all")[-1] == "airas_records"
    assert parse_sources(" arxiv, Airas_Records ") == ["arxiv", "airas_records"]
    with pytest.raises(ValueError, match="Unknown sources: nope"):
        parse_sources("arxiv,nope")
