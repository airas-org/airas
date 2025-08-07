from logging import getLogger
from typing import Any

from pydantic import ValidationError

from airas.services.api_client.retry_policy import (
    HTTPClientFatalError,
    HTTPClientRetryableError,
)
from airas.services.api_client.semantic_scholar_client import SemanticScholarClient
from airas.types.semantic_scholar import SemanticScholarInfo

logger = getLogger(__name__)


class SemanticScholarPaperNormalizer:
    def __init__(self, client: SemanticScholarClient | None = None):
        self.client = client or SemanticScholarClient()

    def _validate_entry(self, entry: dict[str, Any]) -> SemanticScholarInfo | None:
        try:
            authors = []
            for author in entry.get("authors", []):
                author_name = author.get("name", "")
                if author_name:
                    authors.append(author_name)

            external_ids = entry.get("externalIds", {})
            doi = external_ids.get("DOI")
            arxiv_id = external_ids.get("ArXiv")

            return SemanticScholarInfo(
                title=entry.get("title", "No Title"),
                abstract=entry.get("abstract"),
                authors=authors,
                publication_year=entry.get("year"),
                journal=entry.get("venue"),
                doi=doi,
                arxiv_id=arxiv_id,
                arxiv_url=f"https://arxiv.org/abs/{arxiv_id}" if arxiv_id else None,
            )
        except ValidationError as e:
            logger.error(f"Validation error: {e}")
            return None

    def get_by_arxiv_id(self, arxiv_id: str) -> SemanticScholarInfo | None:
        try:
            fields = (
                "paperId",
                "title",
                "abstract",
                "year",
                "authors",
                "venue",
                "externalIds",
                "openAccessPdf",
            )

            response_data = self.client.get_paper_by_arxiv_id(
                arxiv_id=arxiv_id,
                fields=fields,
            )
        except (HTTPClientRetryableError, HTTPClientFatalError) as e:
            logger.warning(f"Semantic Scholar API request failed: {e}")
            return None

        if not response_data:
            return None

        return self._validate_entry(response_data)


def search_ss_by_id(
    arxiv_id: str,
    client: SemanticScholarClient | None = None,
) -> dict | None:
    if not arxiv_id.strip():
        return None

    normalizer = SemanticScholarPaperNormalizer(client)
    paper = normalizer.get_by_arxiv_id(arxiv_id.strip())

    if paper:
        return paper.model_dump()
    return None


if __name__ == "__main__":
    arxiv_id = "1706.03762"  # Attention is All you Need
    results = search_ss_by_id(arxiv_id)
    print(f"results: {results}")
