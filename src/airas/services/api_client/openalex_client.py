import os
from logging import getLogger
from typing import Any, Protocol, runtime_checkable

import requests

from airas.services.api_client.base_http_client import BaseHTTPClient
from airas.services.api_client.response_parser import ResponseParser
from airas.services.api_client.retry_policy import make_retry_policy, raise_for_status

logger = getLogger(__name__)

OPENALEX_RETRY = make_retry_policy()


@runtime_checkable
class ResponseParserProtocol(Protocol):
    def parse(self, response: requests.Response, *, as_: str) -> Any: ...


class OpenAlexClient(BaseHTTPClient):
    def __init__(
        self,
        *,
        base_url: str = "https://api.openalex.org",
        default_headers: dict[str, str] | None = None,
        parser: ResponseParserProtocol | None = None,
    ):
        api_key = os.getenv("OPENALEX_API_KEY")
        params_header = f"?api_key={api_key}" if api_key else ""
        super().__init__(
            base_url=base_url.rstrip("/"),
            default_headers=default_headers or {},
        )
        self._parser = parser or ResponseParser()
        self._key_qs = params_header

    @staticmethod
    def _build_year_filters(year: str | None) -> list[str]:
        if not year:
            return []
        if "-" in year:
            y_from, y_to = year.split("-", 1)
            return [
                f"from_publication_date:{y_from}-01-01",
                f"to_publication_date:{y_to}-12-31",
            ]
        return [f"publication_year:{year}"]

    @OPENALEX_RETRY
    def search_papers(
        self,
        query: str | None = None,
        *,
        title: str | None = None,
        author: str | None = None,
        year: str | None = None,
        per_page: int = 20,
        page: int = 1,
        sort: str | None = "relevance_score:desc",
        fields: tuple[str, ...] | None = None,
        timeout: float = 30.0,
    ) -> dict[str, Any]:
        """
        Search papers using OpenAlex API with flexible search options.

        Args:
            query: Free-text search query (uses default.search filter)
            title: Structured title search (uses display_name.search filter)
            author: Author name search (uses raw_author_name.search filter)
            year: Publication year or year range (e.g., "2020" or "2020-2023")
            per_page: Number of results per page (1-200)
            page: Page number for pagination
            sort: Sort order (default: "relevance_score:desc")
            fields: Fields to include in response
            timeout: Request timeout in seconds

        Returns:
            Dictionary containing search results

        Note:
            - If both query and title/author are provided, structured search (title/author) takes precedence
            - Either query OR title must be provided
        """
        # https://docs.openalex.org/api-entities/works/search-works
        DEFAULT_FIELDS = (
            "id",
            "doi",
            "display_name",
            "publication_year",
            "publication_date",
            "authorships",
            "biblio",
            "primary_location",
            "referenced_works",
            "related_works",
        )

        fields = fields or DEFAULT_FIELDS
        per_page = max(1, min(per_page, 200))

        filters = []

        if title or author:
            if title and title.strip():
                filters.append(f"display_name.search:{title.strip()}")
            if author and author.strip():
                filters.append(f"raw_author_name.search:{author.strip()}")
        elif query and query.strip():
            # Fallback to general search
            filters.append(f"default.search:{query.strip()}")
        else:
            raise ValueError("Either 'query' or 'title' must be provided")

        filters.extend(self._build_year_filters(year))

        params: dict[str, Any] = {
            "page": page,
            "per-page": per_page,
            "select": ",".join(fields),
            "filter": ",".join(filters),
        }

        if sort:
            params["sort"] = sort
        if self._key_qs:
            params["api_key"] = os.getenv("OPENALEX_API_KEY")

        path = "works"
        resp = self.get(path=path, params=params, timeout=timeout)
        raise_for_status(resp, path=path)
        return self._parser.parse(resp, as_="json")


if __name__ == "__main__":
    client = OpenAlexClient()

    # Example 1: General query search
    results1 = client.search_papers(
        query="cnn",
        year="2020-2025",
    )
    print(f"Query search results: {len(results1.get('results', []))} papers found")

    # Example 2: Title-based search
    results2 = client.search_papers(
        title="Attention Is All You Need",
    )
    print(f"Title search results: {len(results2.get('results', []))} papers found")

    # Example 3: Title + Author search
    results3 = client.search_papers(
        title="BERT",
        author="Devlin",
    )
    print(
        f"Title+Author search results: {len(results3.get('results', []))} papers found"
    )
