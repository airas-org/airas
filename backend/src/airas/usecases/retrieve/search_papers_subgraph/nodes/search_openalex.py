import asyncio
import re
from logging import getLogger
from typing import Any

from airas.core.types.paper_search import PaperSearchResult
from airas.infra.openalex_client import OpenAlexClient

logger = getLogger(__name__)

_FIELDS = (
    "id",
    "doi",
    "display_name",
    "publication_date",
    "authorships",
    "primary_location",
    "cited_by_count",
    "best_oa_location",
    "abstract_inverted_index",
)

_ARXIV_URL_PATTERN = re.compile(r"arxiv\.org/(?:pdf|abs)/([0-9]{4}\.[0-9]{4,5})")


def _reconstruct_abstract(inverted_index: dict[str, list[int]] | None) -> str | None:
    """OpenAlex stores abstracts as an inverted index; rebuild the text."""
    if not inverted_index:
        return None
    positioned_words = [
        (position, word)
        for word, positions in inverted_index.items()
        for position in positions
    ]
    positioned_words.sort(key=lambda item: item[0])
    return " ".join(word for _, word in positioned_words)


def _extract_arxiv_id(doi: str | None, pdf_url: str | None) -> str | None:
    if doi and doi.lower().startswith("10.48550/arxiv."):
        return doi[len("10.48550/arxiv.") :]
    if pdf_url and (match := _ARXIV_URL_PATTERN.search(pdf_url)):
        return match.group(1)
    return None


def _normalize_work(work: dict[str, Any]) -> PaperSearchResult:
    openalex_id = (work.get("id") or "").rsplit("/", 1)[-1]
    doi = ((work.get("doi") or "").removeprefix("https://doi.org/")) or None
    best_oa_location = work.get("best_oa_location") or {}
    pdf_url = best_oa_location.get("pdf_url")
    primary_source = (work.get("primary_location") or {}).get("source") or {}
    return PaperSearchResult(
        title=work.get("display_name") or "",
        authors=[
            author_name
            for authorship in work.get("authorships") or []
            if (author_name := (authorship.get("author") or {}).get("display_name"))
        ],
        abstract=_reconstruct_abstract(work.get("abstract_inverted_index")),
        doi=doi,
        arxiv_id=_extract_arxiv_id(doi, pdf_url),
        url=work.get("id"),
        pdf_url=pdf_url,
        published_date=work.get("publication_date"),
        venue=primary_source.get("display_name"),
        citations=work.get("cited_by_count"),
        source="openalex",
        external_ids={"openalex": openalex_id} if openalex_id else {},
    )


async def search_openalex(
    openalex_client: OpenAlexClient,
    query: str,
    max_results: int,
    year: str | None = None,
) -> list[PaperSearchResult]:
    response = await asyncio.to_thread(
        openalex_client.search_papers,
        query,
        year=year,
        per_page=max_results,
        fields=_FIELDS,
    )
    return [_normalize_work(work) for work in response.get("results", [])]
