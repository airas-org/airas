import ast
from logging import getLogger
from typing import Any

from airas.core.types.paper_search import PaperSearchResult
from airas.usecases.retrieve.search_paper_titles_subgraph.nodes.search_paper_titles_from_airas_db import (
    AirasDbPaperSearchIndex,
)

logger = getLogger(__name__)


def _parse_authors(raw_authors: Any) -> list[str]:
    """DB records store authors either as a list or its string repr."""
    if isinstance(raw_authors, list):
        return [str(author) for author in raw_authors]
    if isinstance(raw_authors, str) and raw_authors.startswith("["):
        try:
            parsed = ast.literal_eval(raw_authors)
            if isinstance(parsed, list):
                return [str(author) for author in parsed]
        except (ValueError, SyntaxError):
            pass
    return [raw_authors] if raw_authors else []


def _in_year_range(record_year: str, year: str | None) -> bool:
    if not year or not record_year:
        return True
    if "-" in year:
        year_from, year_to = year.split("-", 1)
        return year_from.strip() <= record_year <= year_to.strip()
    return record_year == year.strip()


def _record_year(record: dict[str, Any]) -> str:
    # Year is stored as a string in some records and an int in others.
    year = record.get("year")
    return str(year) if year else ""


def _normalize_record(record: dict[str, Any]) -> PaperSearchResult:
    paper_url = record.get("paper_url")
    if not paper_url or paper_url == "None":
        paper_url = None
    record_id = record.get("id")
    return PaperSearchResult(
        title=record.get("title") or "",
        authors=_parse_authors(record.get("authors")),
        abstract=record.get("abstract") or None,
        url=paper_url,
        published_date=_record_year(record) or None,
        venue=record.get("conference") or None,
        source="airas_db",
        external_ids={"airas_db": str(record_id)} if record_id else {},
    )


async def search_airas_db(
    search_index: AirasDbPaperSearchIndex,
    query: str,
    max_results: int,
    year: str | None = None,
) -> list[PaperSearchResult]:
    records = await search_index.search_papers(query, max_results)
    return [
        _normalize_record(record)
        for record in records
        if _in_year_range(_record_year(record), year)
    ]
