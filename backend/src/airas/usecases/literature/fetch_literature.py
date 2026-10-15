import asyncio
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from airas.core.research_paths import (
    FULLTEXT_FILENAME,
    PAGE_SEPARATOR,
    RECORD_PATH,
    SOURCE_METADATA_FILENAME,
)
from airas.core.types.paper_search import PaperSearchResult
from airas.infra.airas_db_index import AirasDbPaperSearchIndex
from airas.infra.airas_records_index import AirasRecordsIndex
from airas.infra.arxiv_client import ArxivClient
from airas.infra.openalex_client import OpenAlexClient
from airas.infra.semantic_scholar_client import SemanticScholarClient
from airas.usecases.literature.nodes.fetch_fulltext_from_repository import (
    fetch_fulltext_from_repository,
)
from airas.usecases.literature.nodes.fetch_fulltext_from_url import (
    fetch_fulltext_from_url,
    parser_version,
)
from airas.usecases.literature.search_papers import search_papers


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


# 本文はメタデータと同じ行の pdf_url だけから取る: 別の経路だと版や論文がずれうる
async def _fetch_paper_fulltext(
    paper: PaperSearchResult,
) -> tuple[list[str] | None, dict[str, Any]]:
    url = paper.pdf_url
    if not url:
        return None, {"url": None, "error": "the search source gave no pdf_url"}

    try:
        pages = await fetch_fulltext_from_url(url)
    except Exception as e:
        return None, {"url": url, "error": str(e)}

    if not "".join(pages).strip():
        return None, {"url": url, "error": "no text extracted"}

    return pages, {"url": url, "parser": parser_version(), "fetched_at": _now()}


async def _snapshot_airas_record(
    paper: PaperSearchResult, airas_records_index: AirasRecordsIndex
) -> tuple[list[str], dict[str, Any]]:
    found = await airas_records_index.get(paper.external_ids["airas_record"])
    if found is None:
        raise ValueError(f"{paper.external_ids['airas_record']} left airas-records-db")

    _, pages = await asyncio.to_thread(
        fetch_fulltext_from_repository, found.url, found.commit, [RECORD_PATH]
    )
    return pages, {"url": found.url, "commit": found.commit, "fetched_at": _now()}


async def fetch_literature(
    query: str,
    output_dir: Path,
    *,
    sources: list[str],
    max_results_per_source: int,
    year: str | None,
    openalex_semantic: bool,
    openalex_client: OpenAlexClient,
    semantic_scholar_client: SemanticScholarClient,
    arxiv_client: ArxivClient,
    airas_db_index: AirasDbPaperSearchIndex,
    airas_records_index: AirasRecordsIndex,
) -> None:
    """Every search result as `<output_dir>/<k>/`: metadata.json (the result
    as its search source returned it, the search, how the text was fetched)
    and fulltext.txt when a PDF yielded text, or r1.txt (record.json at the
    commit) for an airas_records study."""
    result = await search_papers(
        query,
        sources=sources,
        max_results_per_source=max_results_per_source,
        year=year,
        openalex_semantic=openalex_semantic,
        openalex_client=openalex_client,
        semantic_scholar_client=semantic_scholar_client,
        arxiv_client=arxiv_client,
        airas_db_index=airas_db_index,
        airas_records_index=airas_records_index,
    )
    # 0 件だと metadata.json が 1 つも書かれず、何を検索して何が落ちたかが残らない
    if not result["papers"]:
        raise RuntimeError(
            f"no search results for {query!r}; errors: {result['search_errors']}"
        )
    search = {
        "query": query,
        "sources": sources,
        "max_results_per_source": max_results_per_source,
        "year": year,
        "openalex_semantic": openalex_semantic,
        "source_results": result["source_results"],
        "search_errors": result["search_errors"],
    }

    for k, paper in enumerate(result["papers"]):
        entry_dir = output_dir / str(k)
        entry_dir.mkdir(parents=True)
        metadata: dict[str, Any] = {
            **paper.model_dump(),
            "search": search,
            "fetched_at": _now(),
        }

        if paper.source == "airas_records":
            try:
                pages, metadata["snapshot"] = await _snapshot_airas_record(
                    paper, airas_records_index
                )
            except Exception as e:
                metadata["snapshot"] = {"error": str(e)}
            else:
                (entry_dir / "r1.txt").write_text(
                    PAGE_SEPARATOR.join(pages), encoding="utf-8"
                )
        else:
            pages, metadata["fulltext"] = await _fetch_paper_fulltext(paper)
            if pages:
                (entry_dir / FULLTEXT_FILENAME).write_text(
                    PAGE_SEPARATOR.join(pages), encoding="utf-8"
                )

        (entry_dir / SOURCE_METADATA_FILENAME).write_text(
            json.dumps(metadata, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
