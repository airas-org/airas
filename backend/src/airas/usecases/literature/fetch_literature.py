import asyncio
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import feedparser

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
from airas.usecases.literature.nodes.search_arxiv import _normalize_entry
from airas.usecases.literature.nodes.search_semantic_scholar import (
    _FIELDS,
    _normalize_item,
)
from airas.usecases.literature.search_papers import search_papers


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def validate_literature_input(
    query: str | None,
    arxiv_ids: list[str] | None,
    dois: list[str] | None,
    *,
    year: str | None = None,
    openalex_semantic: bool = False,
) -> None:
    direct = bool(arxiv_ids or dois)
    if bool(query and query.strip()) == direct:
        raise ValueError("Specify either query or arxiv_ids/dois.")

    if direct and (year or openalex_semantic):
        raise ValueError("year and openalex_semantic apply only to query searches.")

    for arxiv_id in arxiv_ids or []:
        if not re.fullmatch(
            r"(?:\d{4}\.\d{4,5}|[a-z-]+(?:\.[A-Z]{2})?/\d{7})(?:v[1-9]\d*)?",
            arxiv_id.strip(),
        ):
            raise ValueError(f"Invalid arXiv ID: {arxiv_id!r}")

    for doi in dois or []:
        if not re.fullmatch(r"10\.\d{4,9}/\S+", doi.strip()):
            raise ValueError(f"Invalid DOI: {doi!r}")


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
    query: str | None,
    output_dir: Path,
    *,
    arxiv_ids: list[str] | None = None,
    dois: list[str] | None = None,
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
    validate_literature_input(
        query,
        arxiv_ids,
        dois,
        year=year,
        openalex_semantic=openalex_semantic,
    )
    search = None
    requests = [
        *({"arxiv_id": value} for value in arxiv_ids or []),
        *({"doi": value} for value in dois or []),
    ]
    if requests:
        papers = []
        for requested in arxiv_ids or []:
            arxiv_id = requested.strip()
            feed = feedparser.parse(await arxiv_client.aget_paper_by_id(arxiv_id))
            matches = [
                paper
                for entry in feed.entries
                if hasattr(entry, "id") and (paper := _normalize_entry(entry))
            ]
            if len(matches) != 1:
                raise ValueError(f"arXiv did not return one paper for {arxiv_id!r}")
            paper = matches[0]
            resolved = paper.arxiv_id or ""
            if not re.search(r"v\d+$", arxiv_id):
                resolved = re.sub(r"v\d+$", "", resolved)
            if resolved != arxiv_id or not paper.title.strip():
                raise ValueError(f"arXiv returned {paper.arxiv_id!r} for {arxiv_id!r}")
            papers.append(paper)

        for requested in dois or []:
            doi = requested.strip()
            item = await asyncio.to_thread(
                semantic_scholar_client.get_paper_by_doi, doi, fields=_FIELDS
            )
            paper = _normalize_item(item)
            if (
                paper.doi or ""
            ).casefold() != doi.casefold() or not paper.title.strip():
                raise ValueError(
                    f"Semantic Scholar did not return the paper for DOI {doi!r}"
                )
            papers.append(paper)
    else:
        result = await search_papers(
            query or "",
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
        papers = result["papers"]
        search = {
            "query": query,
            "sources": sources,
            "max_results_per_source": max_results_per_source,
            "year": year,
            "openalex_semantic": openalex_semantic,
            "source_results": result["source_results"],
            "search_errors": result["search_errors"],
        }
        # 0 件だと metadata.json が 1 つも書かれず、何を検索して何が落ちたかが残らない
        if not papers:
            raise RuntimeError(
                f"no search results for {query!r}; errors: {result['search_errors']}"
            )
    for k, paper in enumerate(papers):
        entry_dir = output_dir / str(k)
        entry_dir.mkdir(parents=True)
        metadata: dict[str, Any] = {
            **paper.model_dump(),
            "fetched_at": _now(),
        }
        if search is not None:
            metadata["search"] = search
        else:
            metadata["request"] = requests[k]

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
