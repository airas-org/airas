from __future__ import annotations

import asyncio
import logging
import re
from collections.abc import Awaitable, Callable
from typing import Any, TypedDict

from airas.core.types.paper_search import PAPER_SEARCH_SOURCES, PaperSearchResult
from airas.infra.airas_db_index import AirasDbPaperSearchIndex
from airas.infra.airas_records_index import AirasRecordsIndex
from airas.infra.arxiv_client import ArxivClient
from airas.infra.openalex_client import OpenAlexClient
from airas.infra.semantic_scholar_client import SemanticScholarClient
from airas.usecases.literature.nodes.search_airas_db import search_airas_db
from airas.usecases.literature.nodes.search_airas_records import search_airas_records
from airas.usecases.literature.nodes.search_arxiv import search_arxiv
from airas.usecases.literature.nodes.search_openalex import search_openalex
from airas.usecases.literature.nodes.search_semantic_scholar import (
    search_semantic_scholar,
)

logger = logging.getLogger(__name__)


class SourceOutput(TypedDict):
    papers: list[PaperSearchResult]
    error: str | None


def parse_sources(sources: str) -> list[str]:
    if not sources.strip() or sources.strip().lower() == "all":
        return list(PAPER_SEARCH_SOURCES)
    selected = [part.strip().lower() for part in sources.split(",") if part.strip()]
    unknown = sorted(set(selected) - set(PAPER_SEARCH_SOURCES))
    if unknown:
        raise ValueError(
            f"Unknown sources: {', '.join(unknown)}. "
            f"Available: {', '.join(PAPER_SEARCH_SOURCES)} (or 'all')."
        )
    return selected


def dedupe_keys(paper: PaperSearchResult) -> list[str]:
    keys = []
    if paper.doi:
        keys.append(f"doi:{paper.doi.lower()}")
    if paper.arxiv_id:
        keys.append(f"arxiv:{paper.arxiv_id.lower()}")
    if paper.title:
        keys.append(f"title:{re.sub(r'[^a-z0-9]', '', paper.title.lower())}")
    return keys


def merge_missing_fields(kept: PaperSearchResult, duplicate: PaperSearchResult) -> None:
    """Fill fields the kept entry lacks from a duplicate found by another source."""
    for field in (
        "abstract",
        "doi",
        "arxiv_id",
        "url",
        "pdf_url",
        "published_date",
        "venue",
        "citations",
    ):
        if getattr(kept, field) is None and getattr(duplicate, field) is not None:
            setattr(kept, field, getattr(duplicate, field))
    kept.external_ids = {**duplicate.external_ids, **kept.external_ids}


def merge_results(outputs: dict[str, SourceOutput]) -> dict[str, Any]:
    """One list across sources: duplicates merged by DOI, then arXiv id,
    then normalized title, in source order."""
    source_results: dict[str, int] = {}
    search_errors: dict[str, str] = {}
    merged: list[PaperSearchResult] = []
    seen: dict[str, PaperSearchResult] = {}
    for source in PAPER_SEARCH_SOURCES:
        output = outputs.get(source)
        if output is None:
            continue
        if output["error"] is not None:
            search_errors[source] = output["error"]
        source_results[source] = len(output["papers"])
        for paper in output["papers"]:
            keys = dedupe_keys(paper)
            kept = next((seen[key] for key in keys if key in seen), None)
            if kept is None:
                merged.append(paper)
                kept = paper
            else:
                merge_missing_fields(kept, paper)
            for key in dedupe_keys(kept):
                seen[key] = kept
    return {
        "papers": merged,
        "source_results": source_results,
        "search_errors": search_errors,
    }


async def run_source(
    source: str, search: Callable[[], Awaitable[list[PaperSearchResult]]]
) -> tuple[str, SourceOutput]:
    """A source that raises is reported, not fatal to the others."""
    try:
        return source, SourceOutput(papers=await search(), error=None)
    except Exception as e:
        logger.warning(f"Paper search failed for source '{source}': {e}")
        return source, SourceOutput(papers=[], error=str(e))


async def search_papers(
    query: str,
    *,
    sources: list[str],
    max_results_per_source: int,
    year: str | None = None,
    search_mode: str = "keyword",
    verdict: str | None = None,
    stage: str | None = None,
    openalex_client: OpenAlexClient,
    semantic_scholar_client: SemanticScholarClient,
    arxiv_client: ArxivClient,
    airas_db_index: AirasDbPaperSearchIndex,
    airas_records_index: AirasRecordsIndex,
) -> dict[str, Any]:
    semantic = search_mode == "semantic"
    if semantic and (unsupported := sorted(set(sources) - {"openalex"})):
        raise ValueError(
            f"Semantic search is not supported by: {', '.join(unsupported)}. "
            "Only 'openalex' supports semantic search."
        )
    if (verdict or stage) and (others := sorted(set(sources) - {"airas_records"})):
        raise ValueError(
            f"verdict and stage filter airas_records only, not: {', '.join(others)}."
        )
    n = max_results_per_source
    searches: dict[str, Callable[[], Awaitable[list[PaperSearchResult]]]] = {
        "openalex": lambda: search_openalex(
            openalex_client, query, n, year=year, semantic=semantic
        ),
        "semantic_scholar": lambda: search_semantic_scholar(
            semantic_scholar_client, query, n, year=year
        ),
        "arxiv": lambda: search_arxiv(arxiv_client, query, n, year=year),
        "airas_db": lambda: search_airas_db(airas_db_index, query, n, year=year),
        "airas_records": lambda: search_airas_records(
            airas_records_index, query, n, verdict=verdict, stage=stage
        ),
    }
    outputs = dict(
        await asyncio.gather(
            *(run_source(s, searches[s]) for s in PAPER_SEARCH_SOURCES if s in sources)
        )
    )
    return merge_results(outputs)
