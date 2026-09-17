import asyncio
from logging import getLogger
from typing import Any

from airas.core.types.paper_search import PaperSearchResult
from airas.infra.semantic_scholar_client import SemanticScholarClient

logger = getLogger(__name__)

_FIELDS = (
    "paperId",
    "title",
    "abstract",
    "year",
    "publicationDate",
    "authors",
    "venue",
    "citationCount",
    "externalIds",
    "openAccessPdf",
)


def _normalize_item(item: dict[str, Any]) -> PaperSearchResult:
    paper_id = item.get("paperId")
    external = item.get("externalIds") or {}
    open_access_pdf = item.get("openAccessPdf") or {}
    year = item.get("year")
    return PaperSearchResult(
        title=item.get("title") or "",
        authors=[
            name for author in item.get("authors") or [] if (name := author.get("name"))
        ],
        abstract=item.get("abstract"),
        doi=external.get("DOI"),
        arxiv_id=external.get("ArXiv"),
        url=f"https://www.semanticscholar.org/paper/{paper_id}" if paper_id else None,
        pdf_url=open_access_pdf.get("url"),
        published_date=item.get("publicationDate") or (str(year) if year else None),
        venue=item.get("venue") or None,
        citations=item.get("citationCount"),
        source="semantic_scholar",
        external_ids={"semantic_scholar": paper_id} if paper_id else {},
    )


async def search_semantic_scholar(
    semantic_scholar_client: SemanticScholarClient,
    query: str,
    max_results: int,
    year: str | None = None,
) -> list[PaperSearchResult]:
    response = await asyncio.to_thread(
        semantic_scholar_client.search_papers,
        query,
        year=year,
        limit=max_results,
        fields=_FIELDS,
    )
    return [_normalize_item(item) for item in response.get("data") or []]
