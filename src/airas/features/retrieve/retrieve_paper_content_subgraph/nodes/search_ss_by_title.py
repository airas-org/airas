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

            # Try to find PDF URL from openAccessPdf or external sources
            pdf_url = None
            if "openAccessPdf" in entry and entry["openAccessPdf"]:
                pdf_url = entry["openAccessPdf"].get("url")
            elif arxiv_id:
                pdf_url = f"https://arxiv.org/pdf/{arxiv_id}.pdf"

            return PaperProviderSchema(
                title=entry.get("title", "No Title"),
                authors=authors,
                publication_year=str(entry.get("year")) if entry.get("year") else None,
                journal=entry.get("venue"),
                doi=doi,
                arxiv_id=arxiv_id,
                abstract=entry.get("abstract"),
                pdf_url=pdf_url,
            )
        except ValidationError as e:
            logger.error(f"Validation error: {e}")
            return None

    def search_by_title(
        self, title: str, max_results: int | None = None
    ) -> PaperProviderSchema | None:
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

            response_data = self.client.search_papers(
                query=title,
                limit=max_results or 25,
                fields=fields,
            )
        except (HTTPClientRetryableError, HTTPClientFatalError) as e:
            logger.warning(f"Semantic Scholar API request failed: {e}")
            return None

        if not response_data or "data" not in response_data:
            return None

        for entry in response_data["data"]:
            if paper := self._validate_entry(entry):
                return paper  # Return first match
        return None


def search_ss_by_title(
    title: str,
    client: SemanticScholarClient | None = None,
) -> PaperProviderSchema | None:
    if not title.strip():
        return None

    normalizer = SemanticScholarPaperNormalizer(client)
    paper = normalizer.search_by_title(title.strip())

    if paper:
        return paper.model_dump()
    return None


if __name__ == "__main__":
    title = "Attention is All you need"
    results = search_ss_by_title(title)
    print(f"results: {results}")
