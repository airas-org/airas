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
            arxiv_url=f"https://arxiv.org/abs/{arxiv_id}",
        )

    def get_by_id(self, arxiv_id: str) -> PaperProviderSchema | None:
        try:
            xml_feed = self.client.get_paper_by_id(arxiv_id=arxiv_id)
        except (HTTPClientRetryableError, HTTPClientFatalError) as e:
            logger.warning(f"ArXiv API request failed: {e}")
            return None

        feed = feedparser.parse(xml_feed)
        for entry in feed.entries:
            if paper := self._extract_paper_info(entry):
                return paper  # Return first match
        return None


def search_arxiv_by_id(
    arxiv_id: str,
    client: ArxivClient | None = None,
) -> PaperProviderSchema | None:
    if not arxiv_id.strip():
        return None

    normalizer = ArxivPaperNormalizer(client)
    paper = normalizer.get_by_id(arxiv_id.strip())

    if paper:
        return paper.model_dump()
    return None


if __name__ == "__main__":
    arxiv_id = "1706.03762"  # Attention is All you Need
    results = search_arxiv_by_id(arxiv_id)
    print(f"results: {results}")
