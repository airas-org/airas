"""A DOI that resolves to nothing must still try the PDF URL it was given.

bioRxiv hosts its own PDFs and is absent from Semantic Scholar's
open-access index, so the same paper returns `abstract_only` by DOI and
full text by URL. Passing both and getting the abstract is how a paper
nobody read ends up cited as if it had been.

The length cap is here for the other half of the problem: one paper ran to
84k characters, which is enough to crowd out the rest of a session.
"""

from unittest.mock import AsyncMock, patch

import pytest

from airas.usecases.retrieve.fetch_paper_fulltext_subgraph.fetch_paper_fulltext_subgraph import (
    FetchPaperFulltextSubgraph,
    _truncate,
)

DOI_PDF = "https://example.org/oa/paper.pdf"
SUPPLIED_PDF = "https://www.biorxiv.org/content/10.1101/2024.01.01.000000v1.full.pdf"

_MODULE = (
    "airas.usecases.retrieve.fetch_paper_fulltext_subgraph"
    ".fetch_paper_fulltext_subgraph.download_pdf_text"
)


def _subgraph() -> FetchPaperFulltextSubgraph:
    return FetchPaperFulltextSubgraph(semantic_scholar_client=object())


@pytest.mark.asyncio
async def test_supplied_pdf_url_is_tried_when_the_resolved_one_yields_nothing():
    state = {
        "resolved_pdf_url": DOI_PDF,
        "resolved_from": "open_access_pdf",
        "pdf_url": SUPPLIED_PDF,
        "fallback_abstract": "An abstract nobody should settle for.",
    }

    with patch(_MODULE, new=AsyncMock(side_effect=["", "The full text."])) as download:
        result = await _subgraph()._download_and_extract(state)

    assert [call.args[0] for call in download.await_args_list] == [
        DOI_PDF,
        SUPPLIED_PDF,
    ]
    assert result["status"] == "fulltext"
    assert result["resolved_from"] == "pdf_url"
    assert result["text"] == "The full text."


@pytest.mark.asyncio
async def test_the_abstract_is_the_last_resort_not_the_second():
    state = {
        "resolved_pdf_url": DOI_PDF,
        "resolved_from": "open_access_pdf",
        "pdf_url": SUPPLIED_PDF,
        "fallback_abstract": "An abstract.",
    }

    with patch(_MODULE, new=AsyncMock(return_value="")):
        result = await _subgraph()._download_and_extract(state)

    assert result["status"] == "abstract_only"
    assert result["resolved_from"] == "semantic_scholar_abstract"


@pytest.mark.asyncio
async def test_the_same_url_is_not_downloaded_twice():
    state = {
        "resolved_pdf_url": SUPPLIED_PDF,
        "resolved_from": "pdf_url",
        "pdf_url": SUPPLIED_PDF,
    }

    with patch(_MODULE, new=AsyncMock(return_value="")) as download:
        result = await _subgraph()._download_and_extract(state)

    assert download.await_count == 1
    assert result["status"] == "not_found"
    assert result["total_chars"] == 0


@pytest.mark.asyncio
async def test_full_text_is_capped_and_reports_the_full_length():
    state = {
        "resolved_pdf_url": DOI_PDF,
        "resolved_from": "arxiv",
        "max_chars": 10,
    }

    with patch(_MODULE, new=AsyncMock(return_value="x" * 84198)):
        result = await _subgraph()._download_and_extract(state)

    assert result["text"] == "x" * 10
    assert result["total_chars"] == 84198
    assert result["truncated"] is True


def test_truncation_boundaries():
    assert _truncate("abcdef", None) == {
        "text": "abcdef",
        "total_chars": 6,
        "truncated": False,
    }
    # Exactly at the cap is not truncation.
    assert _truncate("abcdef", 6)["truncated"] is False
    assert _truncate("abcdef", 5) == {
        "text": "abcde",
        "total_chars": 6,
        "truncated": True,
    }
    # A nonsensical cap is treated as no cap rather than an empty result.
    assert _truncate("abcdef", 0)["text"] == "abcdef"
