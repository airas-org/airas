import re
from logging import getLogger
from typing import Any

import feedparser
from pydantic import BaseModel, Field, ValidationError

from airas.services.api_client.arxiv_client import ArxivClient
from airas.services.api_client.retry_policy import (
    HTTPClientFatalError,
    HTTPClientRetryableError,
)

logger = getLogger(__name__)


class ArxivResponse(BaseModel):
    arxiv_id: str
    arxiv_url: str
    title: str
    authors: list[str]
    published_date: str
    summary: str = Field(default="No summary")


class ArxivSearcher:
    def __init__(self, client: ArxivClient | None = None):
        self.client = client or ArxivClient()
        self.start_indices: dict[str, int] = {}

    def _validate_entry(self, entry: Any) -> ArxivResponse | None:
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

    def search_by_title(
        self, title: str, max_results: int | None
    ) -> list[ArxivResponse]:
        start_index = self.start_indices.get(title, 0)

        try:
            xml_feed: str = self.client.search_title(
                title=title,
                start=start_index,
                max_results=max_results,
            )
        except (HTTPClientRetryableError, HTTPClientFatalError) as e:
            logger.warning(f"arXiv API request failed: {e}")
            return []

        feed = feedparser.parse(xml_feed)
        papers = [
            paper for entry in feed.entries if (paper := self._validate_entry(entry))
        ]

        if max_results is not None and len(papers) >= max_results:
            self.start_indices[title] = start_index + max_results
        return papers


def search_arxiv_by_titles(
    titles: list[str],
    papers_per_query: int = 1,
    client: ArxivClient | None = None,
) -> list[dict[str, Any]]:
    if not titles:
        logger.warning("No titles provided. Returning empty list.")
        return []

    searcher = ArxivSearcher(client)
    all_papers = []

    for title in titles:
        normalized_title = re.sub(r"\s+", " ", title.lower()).strip()

        found_papers = searcher.search_by_title(
            title=normalized_title,
            max_results=papers_per_query,
        )
        all_papers.extend([p.model_dump() for p in found_papers])

    return all_papers


if __name__ == "__main__":
    titles = [
        "Sin3DM: Learning a Diffusion Model from a Single 3D Textured Shape",
    ]
    results = search_arxiv_by_titles(titles)
    print(f"results: {results}")
