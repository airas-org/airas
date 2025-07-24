from logging import getLogger
from typing import Any

from airas.services.api_client.openalex_client import OpenAlexClient
from airas.services.api_client.retry_policy import (
    HTTPClientFatalError,
    HTTPClientRetryableError,
)
from airas.types.paper_provider_schema import PaperProviderSchema

logger = getLogger(__name__)


class OpenAlexPaperNormalizer:
    def __init__(self, client: OpenAlexClient | None = None):
        self.client = client or OpenAlexClient()

    def _extract_paper_info(self, entry: dict[str, Any]) -> PaperProviderSchema | None:
        # Extract authors
        authors = [
            authorship["author"]["display_name"]
            for authorship in entry.get("authorships", [])
            if authorship.get("author", {}).get("display_name")
        ]

        # Find formal venue (skip repositories/arxiv)
        venue = None
        for location in entry.get("locations", []):
            if location.get("source"):
                source = location["source"]
                source_type = source.get("type", "")
                display_name = source.get("display_name", "")

                if (
                    source_type in ["conference", "journal"]
                    and source_type != "repository"
                    and "arxiv" not in display_name.lower()
                ):
                    venue = display_name
                    break

        # Extract identifiers and URLs
        arxiv_id = entry.get("ids", {}).get("arxiv") if entry.get("ids") else None
        pdf_url = (
            entry.get("open_access", {}).get("oa_url")
            if entry.get("open_access")
            else None
        )

        # Convert abstract inverted index to text
        abstract = None
        abstract_index = entry.get("abstract_inverted_index")
        if abstract_index and isinstance(abstract_index, dict):
            words = sorted(
                abstract_index.keys(),
                key=lambda w: abstract_index[w][0] if abstract_index[w] else 0,
            )
            abstract = " ".join(words)

        return PaperProviderSchema(
            title=entry.get("display_name", "No Title"),
            authors=authors,
            publication_year=str(entry.get("publication_year"))
            if entry.get("publication_year")
            else None,
            journal=venue,
            doi=entry.get("doi"),
            arxiv_id=arxiv_id,
            abstract=abstract,
            pdf_url=pdf_url,
        )

    def search(self, query: str, max_results: int = 1) -> PaperProviderSchema | None:
        try:
            fields = (
                "id",
                "doi",
                "display_name",
                "publication_year",
                "authorships",
                "locations",
                "abstract_inverted_index",
                "open_access",
                "ids",
            )

            response_data = self.client.search_papers(
                query=query,
                per_page=max_results,
                fields=fields,
            )
        except (HTTPClientRetryableError, HTTPClientFatalError) as e:
            logger.warning(f"OpenAlex API request failed: {e}")
            return None

        if not response_data or "results" not in response_data:
            return None

        for entry in response_data["results"]:
            if paper := self._extract_paper_info(entry):
                return paper  # Return first match
        return None


def search_openalex_by_title(
    title: str,
    client: OpenAlexClient | None = None,
) -> PaperProviderSchema | None:
    if not title.strip():
        return None

    normalizer = OpenAlexPaperNormalizer(client)
    paper = normalizer.search(title.strip())

    if paper:
        return paper.model_dump()
    return None


if __name__ == "__main__":
    title = "Attention is All you need"
    results = search_openalex_by_title(title)
    print(f"results: {results}")
