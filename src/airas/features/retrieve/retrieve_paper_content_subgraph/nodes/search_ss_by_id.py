from logging import getLogger
from typing import Any

from pydantic import ValidationError

from airas.services.api_client.retry_policy import (
    HTTPClientFatalError,
    HTTPClientRetryableError,
)
from airas.services.api_client.semantic_scholar_client import SemanticScholarClient
from airas.types.paper_provider_schema import PaperProviderSchema

logger = getLogger(__name__)


class SemanticScholarPaperNormalizer:
    def __init__(self, client: SemanticScholarClient | None = None):
        self.client = client or SemanticScholarClient()

    def _validate_entry(self, entry: dict[str, Any]) -> PaperProviderSchema | None:
        try:
            # Extract author names
            authors = []
            for author in entry.get("authors", []):
                author_name = author.get("name", "")
                if author_name:
                    authors.append(author_name)

            # Extract external IDs
            external_ids = entry.get("externalIds", {})
            doi = external_ids.get("DOI")
            arxiv_id = external_ids.get("ArXiv")

            return PaperProviderSchema(
                title=entry.get("title", "No Title"),
                authors=authors,
                publication_year=str(entry.get("year")) if entry.get("year") else None,
                journal=entry.get("venue"),
                doi=doi,
                arxiv_id=arxiv_id,
                abstract=entry.get("abstract"),
                arxiv_url=f"https://arxiv.org/abs/{arxiv_id}" if arxiv_id else None,
            )
        except ValidationError as e:
            logger.error(f"Validation error: {e}")
            return None

    def get_by_arxiv_id(self, arxiv_id: str) -> PaperProviderSchema | None:
        try:
            # Request only essential fields to keep response minimal like other providers
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

        # For direct lookup, response_data is the paper object, not a list
        return self._validate_entry(response_data)


def search_ss_by_id(
    arxiv_id: str,
    client: SemanticScholarClient | None = None,
) -> PaperProviderSchema | None:
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
