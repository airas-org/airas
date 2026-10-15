"""Sources run side by side; one failing is reported, and duplicates across
sources become one row."""

import asyncio
from typing import Any

import pytest

from airas.core.types.paper_search import PaperSearchResult
from airas.usecases.literature.search_papers import (
    SourceOutput,
    _run_source,
    dedupe_results,
    parse_sources,
)


def _paper(source: str, **fields: object) -> PaperSearchResult:
    return PaperSearchResult(title="Attention Is All You Need", source=source, **fields)


def test_an_arxiv_row_wins_over_unversioned_duplicates() -> None:
    result = dedupe_results(
        {
            "arxiv": SourceOutput(
                papers=[_paper("arxiv", arxiv_id="1706.03762v7")], error=None
            ),
            "openalex": SourceOutput(
                papers=[_paper("openalex", arxiv_id="1706.03762", citations=9)],
                error=None,
            ),
            "semantic_scholar": SourceOutput(papers=[], error="rate limited"),
        }
    )
    (paper,) = result["papers"]
    assert (paper.source, paper.arxiv_id, paper.citations) == (
        "arxiv",
        "1706.03762v7",
        None,
    )
    assert result["source_results"] == {
        "arxiv": 1,
        "openalex": 1,
        "semantic_scholar": 0,
    }
    assert result["search_errors"] == {"semantic_scholar": "rate limited"}


def test_a_duplicate_is_dropped_not_merged() -> None:
    result = dedupe_results(
        {
            "openalex": SourceOutput(
                papers=[_paper("openalex", doi="10.1/a")], error=None
            ),
            "semantic_scholar": SourceOutput(
                papers=[_paper("semantic_scholar", pdf_url="https://x/pdf")],
                error=None,
            ),
        }
    )
    (paper,) = result["papers"]
    assert (paper.source, paper.pdf_url) == ("openalex", None)


def test_a_source_that_raises_is_reported_not_raised() -> None:
    async def boom() -> list[PaperSearchResult]:
        raise RuntimeError("down")

    assert asyncio.run(_run_source("arxiv", boom)) == (
        "arxiv",
        SourceOutput(papers=[], error="down"),
    )


def test_sources_are_parsed_and_unknown_ones_refused() -> None:
    assert parse_sources("all")[-1] == "airas_records"
    assert parse_sources(" arxiv, Airas_Records ") == ["arxiv", "airas_records"]
    with pytest.raises(ValueError, match="Unknown sources: nope"):
        parse_sources("arxiv,nope")


def test_the_graph_path_says_when_it_cannot_search_the_store() -> None:
    from airas.workflows.literature.search_papers_subgraph import (
        SearchPapersSubgraph,
    )

    unused: Any = None
    result = asyncio.run(
        SearchPapersSubgraph(unused, unused, unused, unused)
        .build_graph()
        .ainvoke(
            {
                "query": "x",
                "sources": ["airas_records"],
                "max_results_per_source": 5,
                "year": None,
                "search_mode": "keyword",
            }
        )
    )
    assert result["papers"] == []
    assert "not configured" in result["search_errors"]["airas_records"]
