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


class ArxivNode:
    def __init__(
        self,
        num_retrieve_paper: int = 5,
        period_days: int | None = None,
    ):
        self.num_retrieve_paper = num_retrieve_paper
        self.period_days = period_days
        self.start_indices: dict[str, int] = {}  # TODO: stateに持たせる？
        self.client = ArxivClient()

    def _date_range(self) -> tuple[str, str] | tuple[None, None]:
        if self.period_days is None:
            return None, None
        now_utc = datetime.now(pytz.utc)
        from_date = (now_utc - timedelta(days=self.period_days)).strftime("%Y-%m-%d")
        to_date = now_utc.strftime("%Y-%m-%d")
        return from_date, to_date

    def _validate(self, entry) -> ArxivResponse | None:
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

    def _search_paper(self, query: str) -> list[dict[str, Any]]:
        from_date, to_date = self._date_range()
        start_index = self.start_indices.get(query, 0)

        try:
            xml_feed: str = self.client.search(
                query=query,
                start=start_index,
                max_results=self.num_retrieve_paper,
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
            if (paper := self._validate(entry))
        ]

        if len(papers) == self.num_retrieve_paper:
            self.start_indices[query] = start_index + self.num_retrieve_paper
        return papers

    def execute(self, queries) -> list[dict]:
        if not queries:
            logger.warning("No valid queries. Return empty.")
            return []

        all_papers = []
        for q in queries:
            all_papers.extend(self._search_paper(q))
        return all_papers


if __name__ == "__main__":
    queries = [
        "deep learning",
    ]
    arxiv_node = ArxivNode()
    search_results = arxiv_node.execute(queries)
    print(search_results)
