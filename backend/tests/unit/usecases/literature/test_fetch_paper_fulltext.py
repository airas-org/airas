"""Supplying more identifiers must never produce a worse answer, and the full
text lands in a file the agent reads, never inline."""

from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest

from airas.core.research_paths import PAGE_SEPARATOR
from airas.usecases.literature.fetch_paper_fulltext import fetch_paper_fulltext

ARXIV_ID = "2210.03629"
ARXIV_PDF = f"https://arxiv.org/pdf/{ARXIV_ID}"
DOI = "10.1101/2024.01.01.000000"
OA_PDF = "https://example.org/oa/paper.pdf"
SUPPLIED_PDF = "https://www.biorxiv.org/content/10.1101/2024.01.01.000000v1.full.pdf"
ABSTRACT = "An abstract nobody should settle for."
_DOWNLOAD = "airas.usecases.literature.fetch_paper_fulltext.fetch_fulltext_from_url"


class FakeSemanticScholar:
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


async def _run(client, downloads, cache: Path, **ids) -> tuple[dict, list[str]]:
    pages = [[text] if text else [] for text in downloads]
    with patch(_DOWNLOAD, new=AsyncMock(side_effect=pages)) as download:
        result = await fetch_paper_fulltext(
            semantic_scholar_client=client, cache_dir=cache, **ids
        )
    return result, [call.args[0] for call in download.await_args_list]


async def test_a_doi_that_resolves_to_nothing_still_tries_the_supplied_url(tmp_path):
    client = FakeSemanticScholar(_paper())
    result, requested = await _run(
        client, ["The full text."], tmp_path, doi=DOI, pdf_url=SUPPLIED_PDF
    )
    assert requested == [SUPPLIED_PDF]
    assert result["status"] == "fulltext"
    assert result["resolved_from"] == "pdf_url"
    assert client.calls == []


async def test_a_dead_supplied_url_does_not_cost_the_abstract(tmp_path):
    client = FakeSemanticScholar(_paper())
    result, requested = await _run(
        client, [""], tmp_path, doi=DOI, pdf_url=SUPPLIED_PDF
    )
    assert requested == [SUPPLIED_PDF]
    assert client.calls == [DOI]
    assert result["status"] == "abstract_only"
    assert result["abstract"] == ABSTRACT
    assert result["fulltext_path"] is None


async def test_a_dead_supplied_url_falls_through_to_urls_only_the_doi_knows(tmp_path):
    client = FakeSemanticScholar(_paper(arxiv=ARXIV_ID))
    result, requested = await _run(
        client, ["", "The full text."], tmp_path, doi=DOI, pdf_url=SUPPLIED_PDF
    )
    assert requested == [SUPPLIED_PDF, ARXIV_PDF]
    assert result["status"] == "fulltext"
    assert result["resolved_from"] == "arxiv"


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
    paper, downloads, expected, tmp_path
):
    doi_only, _ = await _run(
        FakeSemanticScholar(paper), downloads[1:] or [""], tmp_path / "a", doi=DOI
    )
    with_url, _ = await _run(
        FakeSemanticScholar(paper),
        downloads,
        tmp_path / "b",
        doi=DOI,
        pdf_url=SUPPLIED_PDF,
    )
    assert doi_only["status"] == expected
    assert with_url["status"] == expected


async def test_a_rate_limited_lookup_leaves_the_direct_candidates_intact(tmp_path):
    result, requested = await _run(
        FakeSemanticScholar(fails=True),
        ["The full text."],
        tmp_path,
        doi=DOI,
        pdf_url=SUPPLIED_PDF,
    )
    assert result["status"] == "fulltext"
    assert requested == [SUPPLIED_PDF]


async def test_a_rate_limited_lookup_reports_not_found_rather_than_raising(tmp_path):
    client = FakeSemanticScholar(fails=True)
    result, _ = await _run(client, [""], tmp_path, doi=DOI, pdf_url=SUPPLIED_PDF)
    assert result["status"] == "not_found"
    assert client.calls == [DOI]


async def test_the_same_url_is_never_downloaded_twice(tmp_path):
    client = FakeSemanticScholar(_paper(oa=SUPPLIED_PDF))
    _, requested = await _run(client, ["", ""], tmp_path, doi=DOI, pdf_url=SUPPLIED_PDF)
    assert requested == [SUPPLIED_PDF]


async def test_an_arxiv_id_is_tried_before_a_supplied_url(tmp_path):
    result, requested = await _run(
        FakeSemanticScholar(_paper()),
        ["The full text."],
        tmp_path,
        arxiv_id=ARXIV_ID,
        pdf_url=SUPPLIED_PDF,
    )
    assert requested == [ARXIV_PDF]
    assert result["resolved_from"] == "arxiv"


async def test_an_arxiv_minted_doi_needs_no_lookup(tmp_path):
    client = FakeSemanticScholar(_paper())
    result, requested = await _run(
        client, ["The full text."], tmp_path, doi=f"10.48550/arXiv.{ARXIV_ID}"
    )
    assert requested == [ARXIV_PDF]
    assert result["status"] == "fulltext"
    assert client.calls == []


async def test_the_text_lands_in_the_cache_and_is_reused(tmp_path):
    """The agent reads the file; a second fetch of the same URL downloads nothing."""
    client = FakeSemanticScholar(_paper())
    pages = ["page one", "page two"]
    with patch(_DOWNLOAD, new=AsyncMock(return_value=pages)) as download:
        first = await fetch_paper_fulltext(
            arxiv_id=ARXIV_ID, semantic_scholar_client=client, cache_dir=tmp_path
        )
        again = await fetch_paper_fulltext(
            arxiv_id=ARXIV_ID, semantic_scholar_client=client, cache_dir=tmp_path
        )
    assert download.await_count == 1
    path = Path(first["fulltext_path"])
    assert path.parent == tmp_path
    assert path.read_text() == PAGE_SEPARATOR.join(pages)
    assert first["total_chars"] == len("page onepage two")
    assert again["fulltext_path"] == first["fulltext_path"]
