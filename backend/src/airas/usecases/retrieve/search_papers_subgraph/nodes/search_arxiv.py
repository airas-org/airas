from logging import getLogger

import feedparser

from airas.core.types.paper_search import PaperSearchResult
from airas.infra.arxiv_client import ArxivClient

logger = getLogger(__name__)


def _year_to_date_range(year: str | None) -> tuple[str | None, str | None]:
    """Convert "2023" or "2020-2023" to arXiv submittedDate bounds."""
    if not year:
        return None, None
    if "-" in year:
        year_from, year_to = year.split("-", 1)
    else:
        year_from = year_to = year
    return f"{year_from.strip()}01010000", f"{year_to.strip()}12312359"


def _normalize_entry(entry: feedparser.FeedParserDict) -> PaperSearchResult:
    versioned_id = entry.id.split("/")[-1]
    arxiv_id = versioned_id.split("v")[0]
    return PaperSearchResult(
        title=(getattr(entry, "title", "") or "").replace("\n", " ").strip(),
        authors=[author.name for author in getattr(entry, "authors", [])],
        abstract=getattr(entry, "summary", None),
        doi=getattr(entry, "arxiv_doi", None),
        arxiv_id=arxiv_id,
        url=f"https://arxiv.org/abs/{arxiv_id}",
        pdf_url=f"https://arxiv.org/pdf/{arxiv_id}",
        published_date=getattr(entry, "published", None),
        venue=getattr(entry, "arxiv_journal_ref", None),
        citations=None,
        source="arxiv",
        external_ids={"arxiv": arxiv_id},
    )


async def search_arxiv(
    arxiv_client: ArxivClient,
    query: str,
    max_results: int,
    year: str | None = None,
) -> list[PaperSearchResult]:
    from_date, to_date = _year_to_date_range(year)
    xml_feed = await arxiv_client.asearch_papers(
        query,
        max_results=max_results,
        from_date=from_date,
        to_date=to_date,
    )
    feed = feedparser.parse(xml_feed)
    return [_normalize_entry(entry) for entry in feed.entries if hasattr(entry, "id")]
