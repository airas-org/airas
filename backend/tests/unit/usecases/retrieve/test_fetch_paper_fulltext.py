"""Supplying more identifiers must never produce a worse answer.

That property was broken in both directions. A DOI outside Semantic
Scholar's open-access index returned `abstract_only` even when the caller
also held a working `pdf_url` — bioRxiv hosts its own PDFs and is absent
from that index. And supplying that `pdf_url` alongside the DOI skipped the
DOI lookup entirely, so a dead URL returned `not_found` where the DOI alone
would at least have returned the abstract.

The length cap is here for the other half of the problem: one paper ran to
84,198 characters, overshot the MCP token ceiling and was spilled to a file
instead of returned.
"""

from unittest.mock import AsyncMock, patch

import pytest

from airas.usecases.retrieve.fetch_paper_fulltext_subgraph.fetch_paper_fulltext_subgraph import (
    FetchPaperFulltextSubgraph,
    _truncate,
)

ARXIV_ID = "2210.03629"
ARXIV_PDF = f"https://arxiv.org/pdf/{ARXIV_ID}"
DOI = "10.1101/2024.01.01.000000"
OA_PDF = "https://example.org/oa/paper.pdf"
SUPPLIED_PDF = "https://www.biorxiv.org/content/10.1101/2024.01.01.000000v1.full.pdf"
ABSTRACT = "An abstract nobody should settle for."

_DOWNLOAD = (
    "airas.usecases.retrieve.fetch_paper_fulltext_subgraph"
    ".fetch_paper_fulltext_subgraph.download_pdf_text"
)


class FakeSemanticScholar:
    """Returns a fixed record, and counts how often it was asked."""

    def __init__(self, paper: dict | None = None, fails: bool = False):
        self._paper = paper if paper is not None else {}
        self._fails = fails
        self.calls: list[str] = []

    def get_paper_by_doi(self, doi: str) -> dict:
        self.calls.append(doi)
        if self._fails:
            raise RuntimeError("429 Too Many Requests")
        return self._paper


def _paper(arxiv: str | None = None, oa: str | None = None, abstract=ABSTRACT) -> dict:
    return {
        "externalIds": {"ArXiv": arxiv} if arxiv else {},
        "openAccessPdf": {"url": oa} if oa else None,
        "abstract": abstract,
    }


async def _run(client, downloads, **inputs) -> tuple[dict, list[str]]:
    """Drive both nodes the way the compiled graph does."""
    subgraph = FetchPaperFulltextSubgraph(semantic_scholar_client=client)
    state = {"arxiv_id": None, "doi": None, "pdf_url": None, **inputs}
    with patch(_DOWNLOAD, new=AsyncMock(side_effect=downloads)) as download:
        state.update(await subgraph._resolve_pdf_url(state))
        result = await subgraph._download_and_extract(state)
    return result, [call.args[0] for call in download.await_args_list]


@pytest.mark.asyncio
async def test_a_doi_that_resolves_to_nothing_still_tries_the_supplied_url():
    client = FakeSemanticScholar(_paper())

    result, requested = await _run(
        client, ["The full text."], doi=DOI, pdf_url=SUPPLIED_PDF
    )

    assert requested == [SUPPLIED_PDF]
    assert result["status"] == "fulltext"
    assert result["resolved_from"] == "pdf_url"
    # The supplied URL worked, so nothing had to be asked of a rate-limited API.
    assert client.calls == []


@pytest.mark.asyncio
async def test_a_dead_supplied_url_does_not_cost_the_abstract():
    """The regression that made passing both identifiers worse than one.

    The supplied URL short-circuited the DOI lookup, so a URL that returned
    nothing produced `not_found` — while the DOI alone produced the abstract.
    """
    client = FakeSemanticScholar(_paper())

    result, requested = await _run(client, [""], doi=DOI, pdf_url=SUPPLIED_PDF)

    assert requested == [SUPPLIED_PDF]
    assert client.calls == [DOI]
    assert result["status"] == "abstract_only"
    assert result["text"] == ABSTRACT


@pytest.mark.asyncio
async def test_a_dead_supplied_url_falls_through_to_urls_only_the_doi_knows():
    """An abstract is not good enough if the DOI can still reach full text."""
    client = FakeSemanticScholar(_paper(arxiv=ARXIV_ID))

    result, requested = await _run(
        client, ["", "The full text."], doi=DOI, pdf_url=SUPPLIED_PDF
    )

    assert requested == [SUPPLIED_PDF, ARXIV_PDF]
    assert result["status"] == "fulltext"
    assert result["resolved_from"] == "arxiv"


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("paper", "downloads", "expected"),
    [
        (_paper(arxiv=ARXIV_ID), ["", "text"], "fulltext"),
        (_paper(oa=OA_PDF), ["", "text"], "fulltext"),
        (_paper(), [""], "abstract_only"),
        (_paper(abstract=None), [""], "not_found"),
    ],
)
async def test_adding_a_pdf_url_never_downgrades_the_outcome(
    paper, downloads, expected
):
    """The property, stated directly: extra identifiers only ever help."""
    doi_only, _ = await _run(FakeSemanticScholar(paper), downloads[1:] or [""], doi=DOI)
    with_url, _ = await _run(
        FakeSemanticScholar(paper), downloads, doi=DOI, pdf_url=SUPPLIED_PDF
    )

    assert doi_only["status"] == expected
    assert with_url["status"] == expected


@pytest.mark.asyncio
async def test_a_rate_limited_lookup_leaves_the_direct_candidates_intact():
    """Semantic Scholar 429s constantly; that must not lose a working URL."""
    client = FakeSemanticScholar(fails=True)

    result, requested = await _run(
        client, ["The full text."], doi=DOI, pdf_url=SUPPLIED_PDF
    )

    assert result["status"] == "fulltext"
    assert requested == [SUPPLIED_PDF]


@pytest.mark.asyncio
async def test_a_rate_limited_lookup_reports_not_found_rather_than_raising():
    client = FakeSemanticScholar(fails=True)

    result, _ = await _run(client, [""], doi=DOI, pdf_url=SUPPLIED_PDF)

    assert result["status"] == "not_found"
    assert client.calls == [DOI]


@pytest.mark.asyncio
async def test_the_same_url_is_never_downloaded_twice():
    client = FakeSemanticScholar(_paper(oa=SUPPLIED_PDF))

    _, requested = await _run(client, ["", ""], doi=DOI, pdf_url=SUPPLIED_PDF)

    assert requested == [SUPPLIED_PDF]


@pytest.mark.asyncio
async def test_an_arxiv_id_is_tried_before_a_supplied_url():
    client = FakeSemanticScholar(_paper())

    result, requested = await _run(
        client, ["The full text."], arxiv_id=ARXIV_ID, pdf_url=SUPPLIED_PDF
    )

    assert requested == [ARXIV_PDF]
    assert result["resolved_from"] == "arxiv"


@pytest.mark.asyncio
async def test_an_arxiv_minted_doi_needs_no_lookup():
    client = FakeSemanticScholar(_paper())

    result, requested = await _run(
        client, ["The full text."], doi=f"10.48550/arXiv.{ARXIV_ID}"
    )

    assert requested == [ARXIV_PDF]
    assert result["status"] == "fulltext"
    assert client.calls == []


@pytest.mark.asyncio
async def test_full_text_is_capped_and_reports_the_full_length():
    client = FakeSemanticScholar(_paper())

    result, _ = await _run(client, ["x" * 84198], arxiv_id=ARXIV_ID, max_chars=10)

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
