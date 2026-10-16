"""fetch-literature writes every search result as <output_dir>/<k>/: the row as
its search source returned it, with the text fetched from that row's own
pdf_url when one yields text."""

import asyncio
import json
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest

from airas.core.types.paper_search import PaperSearchResult
from airas.usecases.literature import fetch_literature as module

ARXIV = PaperSearchResult(
    title="Attention Is All You Need",
    arxiv_id="1706.03762v7",
    pdf_url="https://arxiv.org/pdf/1706.03762v7",
    doi="10.48550/arXiv.1706.03762",
    source="arxiv",
)
NO_PDF = PaperSearchResult(title="No PDF Here", doi="10.1/x", source="openalex")
BROKEN = PaperSearchResult(
    title="Broken PDF",
    pdf_url="https://example.org/broken.pdf",
    source="semantic_scholar",
)
STUDY = PaperSearchResult(
    title="SAM on CIFAR",
    source="airas_records",
    external_ids={"airas_record": "auto-res2/sam-cifar@" + "b" * 40},
)


class _Found:
    url = "https://github.com/auto-res2/sam-cifar"
    commit = "b" * 40


class _Records:
    async def get(self, record_id: str) -> Any:
        return _Found()


def _run(
    tmp_path: Path, papers: list[PaperSearchResult], monkeypatch, **options
) -> Path:
    async def search(query: str, **kw: Any) -> dict[str, Any]:
        assert not options.get("arxiv_ids") and not options.get("dois")
        return {
            "papers": papers,
            "source_results": {"arxiv": len(papers)},
            "search_errors": {"semantic_scholar": "rate limited"},
        }

    async def fetch(url: str) -> list[str]:
        if "broken" in url:
            raise ValueError("not a PDF")
        return ["page one", "page two"]

    monkeypatch.setattr(module, "search_papers", search)
    monkeypatch.setattr(module, "fetch_fulltext_from_url", fetch)
    monkeypatch.setattr(
        module,
        "fetch_fulltext_from_repository",
        lambda url, commit, files: ({}, ["==> .research/record.json <==\n{}"]),
    )
    monkeypatch.setattr(module, "parser_version", lambda: "pymupdf test")
    args: dict[str, Any] = {
        "query": "transformer",
        "output_dir": tmp_path / "literature",
        "sources": ["arxiv"],
        "max_results_per_source": 5,
        "year": None,
        "openalex_semantic": False,
        "openalex_client": None,
        "semantic_scholar_client": None,
        "arxiv_client": None,
        "airas_db_index": None,
        "airas_records_index": _Records(),
        **options,
    }
    asyncio.run(module.fetch_literature(**args))
    return tmp_path / "literature"


def _metadata(entry_dir: Path) -> dict[str, Any]:
    return json.loads((entry_dir / "metadata.json").read_text())


def test_every_result_is_written_with_its_row_and_the_search(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    out = _run(tmp_path, [ARXIV, NO_PDF], monkeypatch)

    first = _metadata(out / "0")
    assert (first["title"], first["arxiv_id"], first["source"]) == (
        "Attention Is All You Need",
        "1706.03762v7",
        "arxiv",
    )
    assert first["search"]["query"] == "transformer"
    assert first["search"]["search_errors"] == {"semantic_scholar": "rate limited"}
    assert first["fetched_at"].endswith("+00:00")
    assert (out / "0" / "fulltext.txt").read_text() == "page one\fpage two"
    assert first["fulltext"]["url"] == "https://arxiv.org/pdf/1706.03762v7"
    assert first["fulltext"]["parser"] == "pymupdf test"


def test_a_result_without_a_text_is_kept_with_the_reason(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    out = _run(tmp_path, [NO_PDF, BROKEN], monkeypatch)

    assert _metadata(out / "0")["fulltext"] == {
        "url": None,
        "error": "the search source gave no pdf_url",
    }
    assert _metadata(out / "1")["fulltext"] == {
        "url": "https://example.org/broken.pdf",
        "error": "not a PDF",
    }
    assert not (out / "0" / "fulltext.txt").exists()
    assert not (out / "1" / "fulltext.txt").exists()


def test_an_airas_study_is_its_record_at_the_commit(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    out = _run(tmp_path, [STUDY], monkeypatch)

    snapshot = _metadata(out / "0")["snapshot"]
    assert (snapshot["url"], snapshot["commit"]) == (_Found.url, "b" * 40)
    assert (out / "0" / "r1.txt").read_text().startswith("==> .research/record.json")


def test_no_result_at_all_fails_the_run(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    with pytest.raises(RuntimeError, match="no search results"):
        _run(tmp_path, [], monkeypatch)


def _arxiv_feed(arxiv_id: str) -> str:
    return (
        '<feed xmlns="http://www.w3.org/2005/Atom"><entry>'
        f"<id>http://arxiv.org/abs/{arxiv_id}</id><title>A paper</title>"
        "<author><name>An author</name></author></entry></feed>"
    )


@pytest.mark.parametrize("arxiv_id", ["1706.03762v1", "1706.03762", "hep-th/9901001v1"])
@pytest.mark.parametrize("with_doi", [False, True])
def test_direct_arxiv_fetch_records_the_requested_id_and_resolved_version(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, arxiv_id: str, with_doi: bool
) -> None:
    resolved = arxiv_id if "v" in arxiv_id else arxiv_id + "v7"

    async def get_paper(requested: str) -> str:
        assert requested == arxiv_id
        return _arxiv_feed(resolved)

    out = _run(
        tmp_path,
        [],
        monkeypatch,
        query=None,
        arxiv_ids=[arxiv_id],
        arxiv_client=SimpleNamespace(aget_paper_by_id=get_paper),
        dois=["10.18653/v1/N18-3011"] if with_doi else [],
        semantic_scholar_client=SimpleNamespace(
            get_paper_by_doi=lambda doi, **kw: {
                "title": "A DOI paper",
                "externalIds": {"DOI": doi},
            }
        ),
    )
    metadata = _metadata(out / "0")
    assert metadata["request"] == {"arxiv_id": arxiv_id}
    assert metadata["arxiv_id"] == resolved
    assert metadata["fulltext"]["url"] == f"https://arxiv.org/pdf/{resolved}"
    assert (out / "0" / "fulltext.txt").read_text() == "page one\fpage two"
    assert "search" not in metadata
    if with_doi:
        assert _metadata(out / "1")["request"] == {"doi": "10.18653/v1/N18-3011"}


@pytest.mark.parametrize("pdf_url", [None, "https://example.org/paper.pdf"])
def test_direct_doi_fetch_uses_matching_metadata_and_preserves_missing_text(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, pdf_url: str | None
) -> None:
    doi = "10.18653/v1/N18-3011"

    def get_paper(requested: str, **kwargs: Any) -> dict[str, Any]:
        assert requested == doi
        return {
            "title": "A DOI paper",
            "externalIds": {"DOI": doi.lower()},
            "publicationDate": "2018-06-01",
            "openAccessPdf": {"url": pdf_url},
        }

    out = _run(
        tmp_path,
        [],
        monkeypatch,
        query=None,
        dois=[doi],
        semantic_scholar_client=SimpleNamespace(get_paper_by_doi=get_paper),
    )
    metadata = _metadata(out / "0")
    assert metadata["request"] == {"doi": doi}
    assert metadata["doi"] == doi.lower()
    assert metadata["published_date"] == "2018-06-01"
    assert (out / "0" / "fulltext.txt").exists() == bool(pdf_url)
    if pdf_url is None:
        assert "error" in metadata["fulltext"]


@pytest.mark.parametrize("returned_id", ["1706.03762v7", "1706.03763v1", None])
def test_direct_fetch_rejects_a_different_paper_or_version_before_writing(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, returned_id: str | None
) -> None:
    async def get_paper(requested: str) -> str:
        return _arxiv_feed(returned_id) if returned_id else "<feed/>"

    with pytest.raises(ValueError, match="arXiv"):
        _run(
            tmp_path,
            [],
            monkeypatch,
            query=None,
            arxiv_ids=["1706.03762v1"],
            arxiv_client=SimpleNamespace(aget_paper_by_id=get_paper),
        )
    assert not (tmp_path / "literature").exists()


@pytest.mark.parametrize("returned_doi", [None, "10.18653/v1/D18-2012"])
def test_direct_doi_fetch_rejects_missing_or_different_identifiers(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, returned_doi: str | None
) -> None:
    def get_paper(*args: Any, **kwargs: Any) -> dict[str, Any]:
        return {"title": "Another paper", "externalIds": {"DOI": returned_doi}}

    with pytest.raises(ValueError, match="DOI"):
        _run(
            tmp_path,
            [],
            monkeypatch,
            query=None,
            dois=["10.18653/v1/N18-3011"],
            semantic_scholar_client=SimpleNamespace(get_paper_by_doi=get_paper),
        )
    assert not (tmp_path / "literature").exists()


@pytest.mark.parametrize(
    ("query", "arxiv_ids", "dois", "options"),
    [
        (None, None, None, {}),
        (" ", [], [], {}),
        ("query", ["1706.03762"], None, {}),
        ("query", None, ["10.18653/v1/N18-3011"], {}),
        (None, [""], None, {}),
        (None, ["1706.03762v0"], None, {}),
        (None, None, ["not a DOI"], {}),
        (None, ["1706.03762"], None, {"year": "2025"}),
        (None, ["1706.03762"], None, {"openalex_semantic": True}),
    ],
)
def test_invalid_or_ambiguous_requests_are_rejected(
    query, arxiv_ids, dois, options
) -> None:
    with pytest.raises(ValueError):
        module.validate_literature_input(query, arxiv_ids, dois, **options)
