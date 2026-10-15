import re
from logging import getLogger

import feedparser

from airas.core.types.paper_search import PaperSearchResult
from airas.infra.arxiv_client import ArxivClient

logger = getLogger(__name__)

# 2007 年 4 月より前の旧形式 id (hep-th/9901001v1) は扱わない
_NEW_STYLE_VERSIONED_ID = re.compile(r"/abs/(\d{4}\.\d{4,5}v\d+)$")


def _year_to_date_range(year: str | None) -> tuple[str | None, str | None]:
    """Convert "2023" or "2020-2023" to arXiv submittedDate bounds."""
    if not year:
        return None, None
    if "-" in year:
        year_from, year_to = year.split("-", 1)
    else:
        year_from = year_to = year
    return f"{year_from.strip()}01010000", f"{year_to.strip()}12312359"


def _normalize_entry(entry: feedparser.FeedParserDict) -> PaperSearchResult | None:
    if not (match := _NEW_STYLE_VERSIONED_ID.search(entry.id)):
        return None
    arxiv_id = match.group(1)
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
    return [
        paper
        for entry in feed.entries
        if hasattr(entry, "id") and (paper := _normalize_entry(entry))
    ]
