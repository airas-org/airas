from logging import getLogger
from typing import Any

import feedparser

from airas.services.api_client.arxiv_client import ArxivClient
from airas.services.api_client.retry_policy import (
    HTTPClientFatalError,
    HTTPClientRetryableError,
)
from airas.types.paper_provider_schema import PaperProviderSchema

logger = getLogger(__name__)


class ArxivPaperNormalizer:
    def __init__(self, client: ArxivClient | None = None):
        self.client = client or ArxivClient()

    def _extract_paper_info(self, entry: Any) -> PaperProviderSchema | None:
        if not hasattr(entry, "id"):
            return None

        arxiv_id = entry.id.split("/")[-1]

        # Extract year from published date
        year = None
        if hasattr(entry, "published"):
            try:
                year = int(entry.published[:4])
            except (ValueError, IndexError):
                pass

        # Extract DOI if available
        doi = None
        if hasattr(entry, "links"):
            for link in entry.links:
                if link.get("title") == "doi":
                    doi = link.get("href", "").replace("http://dx.doi.org/", "")
                    break

        return PaperProviderSchema(
            title=entry.title or "No Title",
            authors=[a.name for a in getattr(entry, "authors", [])],
            publication_year=str(year) if year else None,
            journal=None,  # ArXiv is not a formal journal
            doi=doi,
            arxiv_id=arxiv_id,
            abstract=getattr(entry, "summary", None),
            pdf_url=f"https://arxiv.org/pdf/{arxiv_id}.pdf",
        )

    def search(self, query: str, max_results: int = 1) -> PaperProviderSchema | None:
        try:
            xml_feed = self.client.search_papers(
                query=query,
                max_results=max_results,
            )
        except (HTTPClientRetryableError, HTTPClientFatalError) as e:
            logger.warning(f"ArXiv API request failed: {e}")
            return None

        feed = feedparser.parse(xml_feed)
        for entry in feed.entries:
            if paper := self._extract_paper_info(entry):
                return paper  # Return first match
        return None


def search_arxiv_by_title(
    title: str,
    client: ArxivClient | None = None,
) -> PaperProviderSchema | None:
    if not title.strip():
        return None

    normalizer = ArxivPaperNormalizer(client)
    paper = normalizer.search(title.strip())

    if paper:
        return paper.model_dump()
    return None


if __name__ == "__main__":
    title = "Attention is All you need"
    results = search_arxiv_by_title(title)
    print(f"results: {results}")
