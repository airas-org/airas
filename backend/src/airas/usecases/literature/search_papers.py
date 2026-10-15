from __future__ import annotations

import asyncio
import logging
import re
import unicodedata
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


# TODO: 同一論文のバージョン違いが考慮されているか
def _keys_identifying_paper(paper: PaperSearchResult) -> list[str]:
    keys = []
    if paper.doi:
        keys.append(f"doi:{paper.doi.lower()}")
    if paper.arxiv_id:
        # 版を外し、版の分からない他ソースの同じ論文とも一致させる
        keys.append("arxiv:" + re.sub(r"v\d+$", "", paper.arxiv_id.lower()))
    # 英数字だけ残すと英語以外のタイトルが空になり、別の論文同士が一致してしまう
    if title := re.sub(
        r"[\W_]", "", unicodedata.normalize("NFKC", paper.title or "").casefold()
    ):
        keys.append(f"title:{title}")
    return keys


def dedupe_results(outputs: dict[str, SourceOutput]) -> dict[str, Any]:
    """One list across sources: a paper found again by the same DOI, arXiv id
    (any version) or normalized title is dropped; the earlier source keeps it."""
    source_results: dict[str, int] = {}
    search_errors: dict[str, str] = {}
    deduped: list[PaperSearchResult] = []
    seen: set[str] = set()

    for source in PAPER_SEARCH_SOURCES:
        output = outputs.get(source)
        if output is None:
            continue

        if output["error"] is not None:
            search_errors[source] = output["error"]

        source_results[source] = len(output["papers"])
        for paper in output["papers"]:
            keys = _keys_identifying_paper(paper)
            if seen.isdisjoint(keys):
                deduped.append(paper)
            seen.update(keys)
    return {
        "papers": deduped,
        "source_results": source_results,
        "search_errors": search_errors,
    }


async def _run_source(
    source: str, search: Callable[[], Awaitable[list[PaperSearchResult]]]
) -> tuple[str, SourceOutput]:
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
    # True でも embedding 検索になるのは openalex だけ、他のソースは常に keyword
    openalex_semantic: bool = False,
    openalex_client: OpenAlexClient,
    semantic_scholar_client: SemanticScholarClient,
    arxiv_client: ArxivClient,
    airas_db_index: AirasDbPaperSearchIndex,
    airas_records_index: AirasRecordsIndex,
) -> dict[str, Any]:
    if openalex_semantic and "openalex" not in sources:
        raise ValueError("openalex_semantic requires 'openalex' in sources.")

    n = max_results_per_source
    searches: dict[str, Callable[[], Awaitable[list[PaperSearchResult]]]] = {
        "openalex": lambda: search_openalex(
            openalex_client, query, n, year=year, semantic=openalex_semantic
        ),
        "semantic_scholar": lambda: search_semantic_scholar(
            semantic_scholar_client, query, n, year=year
        ),
        "arxiv": lambda: search_arxiv(arxiv_client, query, n, year=year),
        "airas_db": lambda: search_airas_db(airas_db_index, query, n, year=year),
        "airas_records": lambda: search_airas_records(airas_records_index, query, n),
    }

    outputs = dict(
        await asyncio.gather(
            *(_run_source(s, searches[s]) for s in PAPER_SEARCH_SOURCES if s in sources)
        )
    )
    return dedupe_results(outputs)
