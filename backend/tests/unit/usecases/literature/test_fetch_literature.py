"""fetch-literature writes every search result as <output_dir>/<k>/: the row as
its search source returned it, with the text fetched from that row's own
pdf_url when one yields text."""

import asyncio
import json
from pathlib import Path
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


def _run(tmp_path: Path, papers: list[PaperSearchResult], monkeypatch) -> Path:
    async def search(query: str, **kw: Any) -> dict[str, Any]:
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
    unused: Any = None
    asyncio.run(
        module.fetch_literature(
            "transformer",
            tmp_path / "literature",
            sources=["arxiv"],
            max_results_per_source=5,
            year=None,
            openalex_semantic=False,
            openalex_client=unused,
            semantic_scholar_client=unused,
            arxiv_client=unused,
            airas_db_index=unused,
            airas_records_index=_Records(),
        )
    )
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
