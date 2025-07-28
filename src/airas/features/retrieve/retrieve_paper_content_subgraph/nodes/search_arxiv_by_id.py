from logging import getLogger
from typing import Any

import feedparser

from airas.services.api_client.arxiv_client import ArxivClient
from airas.services.api_client.retry_policy import (
    HTTPClientFatalError,
    HTTPClientRetryableError,
)
from airas.types.arxiv import ArxivInfo

logger = getLogger(__name__)


class ArxivPaperNormalizer:
    def __init__(self, client: ArxivClient | None = None):
        self.client = client or ArxivClient()

    def _validate_entry(self, entry: Any) -> ArxivInfo | None:
        if not hasattr(entry, "id"):
            return None

        arxiv_id = entry.id.split("/")[-1]

        doi = None
        if hasattr(entry, "arxiv_doi"):
            doi = entry.arxiv_doi
        elif hasattr(entry, "links"):
            for link in entry.links:
                if link.get("title") == "doi":
                    doi = link.get("href", "").replace("http://dx.doi.org/", "")
                    break

        journal_ref = None
        if hasattr(entry, "arxiv_journal_ref"):
            journal_ref = entry.arxiv_journal_ref

        affiliations = []
        if hasattr(entry, "authors"):
            for author in entry.authors:
                if hasattr(author, "arxiv_affiliation"):
                    affiliations.append(author.arxiv_affiliation)

        return ArxivInfo(
            id=arxiv_id,
            url=f"https://arxiv.org/abs/{arxiv_id}",
            title=entry.title or "No Title",
            authors=[a.name for a in getattr(entry, "authors", [])],
            published_date=entry.published if hasattr(entry, "published") else "",
            summary=getattr(entry, "summary", ""),
            journal=journal_ref,  # Use journal_ref instead of None
            doi=doi,
            affiliation=", ".join(affiliations) if affiliations else None,
        )

    def get_by_id(self, arxiv_id: str) -> ArxivInfo | None:
        try:
            xml_feed = self.client.get_paper_by_id(arxiv_id=arxiv_id)
        except (HTTPClientRetryableError, HTTPClientFatalError) as e:
            logger.warning(f"ArXiv API request failed: {e}")
            return None

        feed = feedparser.parse(xml_feed)
        for entry in feed.entries:
            if paper := self._validate_entry(entry):
                return paper
        return None


def search_arxiv_by_id(
    arxiv_id: str,
    client: ArxivClient | None = None,
) -> dict | None:
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
