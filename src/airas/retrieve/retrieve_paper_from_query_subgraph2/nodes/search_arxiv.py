from datetime import datetime, timedelta
from logging import getLogger
from typing import Any

import feedparser
import pytz
from pydantic import BaseModel, Field, ValidationError

from airas.utils.api_client.arxiv_client import (
    ArxivClient,
    ArxivClientFatalError,
    ArxivClientRetryableError,
)

logger = getLogger(__name__)


class ArxivResponse(BaseModel):
    arxiv_id: str
    arxiv_url: str
    title: str
    authors: list[str]
    published_date: str
    summary: str = Field(default="No summary")


_start_indices: dict[str, int] = {} 

def _get_date_range(period_days: int | None) -> tuple[str, str] | tuple[None, None]:
    if period_days is None:
        return None, None
    now_utc = datetime.now(pytz.utc)
    from_date = (now_utc - timedelta(days=period_days)).strftime("%Y-%m-%d")
    to_date = now_utc.strftime("%Y-%m-%d")
    return from_date, to_date


def _validate_entry(entry: Any) -> ArxivResponse | None:
    try:
        return ArxivResponse(
            arxiv_id=entry.id.split("/")[-1],
            arxiv_url=entry.id,
            title=entry.title or "No Title",
            authors=[a.name for a in getattr(entry, "authors", [])],
            published_date=getattr(entry, "published", "Unknown date"),
            summary=getattr(entry, "summary", "No summary"),
        )
    except ValidationError as e:
        logger.error(f"Validation error: {e}")
        return None


def _search_papers(
    query: str, 
    num_retrieve_paper: int, 
    period_days: int | None, 
    client: ArxivClient
) -> list[dict[str, Any]]:
    from_date, to_date = _get_date_range(period_days)
    start_index = _start_indices.get(query, 0)

    try:
        xml_feed: str = client.search(
            query=query,
            start=start_index,
            max_results=num_retrieve_paper,
            from_date=from_date,
            to_date=to_date,
        )
    except (ArxivClientRetryableError, ArxivClientFatalError) as e:
        logger.warning(f"arXiv API request failed: {e}")
        return []
    
    feed = feedparser.parse(xml_feed)
    papers = [
        paper.model_dump()
        for entry in feed.entries
        if (paper := _validate_entry(entry))
    ]

    if len(papers) == num_retrieve_paper:
        _start_indices[query] = start_index + num_retrieve_paper
    return papers


def search_arxiv(
    queries: list[str], 
    num_retrieve_paper: int = 5, 
    period_days: int | None = None, 
    client: ArxivClient | None = None, 
) -> list[dict[str, Any]]:
    if client is None:
        client = ArxivClient()
    if not queries:
        logger.warning("No queries provided. Returning empty list.")
        return []
    
    all_papers = []
    for query in queries:
        all_papers.extend(
            _search_papers(
                query, 
                num_retrieve_paper, 
                period_days, 
                client, 
            )
        )
    return all_papers