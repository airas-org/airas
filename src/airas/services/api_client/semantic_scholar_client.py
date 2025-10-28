import os
from logging import getLogger
from typing import Any, Protocol, runtime_checkable

import httpx
import requests  # type: ignore[import-untyped]

from airas.services.api_client.base_http_client import BaseHTTPClient
from airas.services.api_client.response_parser import ResponseParser
from airas.services.api_client.retry_policy import make_retry_policy, raise_for_status

logger = getLogger(__name__)

SEMANTIC_SCHOLAR_RETRY = make_retry_policy()


@runtime_checkable
class ResponseParserProtocol(Protocol):
    def parse(self, response: requests.Response, *, as_: str) -> Any: ...


class SemanticScholarClient(BaseHTTPClient):
    def __init__(
        self,
        *,
        base_url: str = "https://api.semanticscholar.org/graph/v1",
        default_headers: dict[str, str] | None = None,
        parser: ResponseParserProtocol | None = None,
        sync_session: requests.Session | None = None,
        async_session: httpx.AsyncClient | None = None,
    ):
        api_key: str | None = os.getenv("SEMANTIC_SCHOLAR_API_KEY")
        headers = default_headers or {}

        # API key is optional for Semantic Scholar
        if api_key:
            headers["x-api-key"] = api_key

        super().__init__(
            base_url=base_url.rstrip("/"),
            default_headers=headers,
            sync_session=sync_session,
            async_session=async_session,
        )
        self._parser = parser or ResponseParser()

    @SEMANTIC_SCHOLAR_RETRY
    def search_papers(
        self,
        query: str | None = None,
        *,
        title: str | None = None,
        author: str | None = None,
        year: str | None = None,
        venue: str | None = None,
        limit: int = 20,
        offset: int = 0,
        fields: tuple[str, ...] | None = None,
        timeout: float = 30.0,
    ) -> dict[str, Any]:
        """
        Search papers using Semantic Scholar API with flexible search options.

        Args:
            query: Free-text search query
            title: Title-specific search
            author: Author name search
            year: Publication year filter
            venue: Venue/journal filter
            limit: Maximum number of results to return (1-100)
            offset: Starting index for pagination
            fields: Fields to include in response
            timeout: Request timeout in seconds

        Returns:
            Dictionary containing search results

        Note:
            - If title/author are provided, structured search takes precedence over general query
            - Either query OR title must be provided
        """
        DEFAULT_FIELDS = (
            "paperId",
            "title",
            "abstract",
            "year",
            "authors",
            "venue",
            "citationCount",
            "referenceCount",
            "references",
            "citations",
            "externalIds",
        )

        fields = fields or DEFAULT_FIELDS
        limit = max(1, min(limit, 100))

        search_parts = []
        if title or author:
            if title and title.strip():
                search_parts.append(f"title:{title.strip()}")

            if author and author.strip():
                search_parts.append(f"author:{author.strip()}")

        elif query and query.strip():
            search_parts.append(query.strip())
        else:
            raise ValueError("Either 'query' or 'title' must be provided")

        search_query = " ".join(search_parts)

        filters = []
        if year:
            if "-" in year:
                year_from, year_to = year.split("-", 1)
                filters.append(f"year:{year_from}-{year_to}")
            else:
                filters.append(f"year:{year}")

        if venue:
            filters.append(f"venue:{venue}")

        params: dict[str, Any] = {
            "query": search_query,
            "limit": limit,
            "offset": offset,
            "fields": ",".join(fields),
        }

        if filters:
            params["query"] = f"{search_query} {' '.join(filters)}"

        path = "paper/search"
        resp = self.get(path=path, params=params, timeout=timeout)
        raise_for_status(resp, path=path)
        return self._parser.parse(resp, as_="json")

    @SEMANTIC_SCHOLAR_RETRY
    def get_paper_by_arxiv_id(
        self,
        arxiv_id: str,
        *,
        fields: tuple[str, ...] | None = None,
        timeout: float = 30.0,
    ) -> dict[str, Any]:
        """
        Get paper details by arXiv ID using Semantic Scholar API.

        Args:
            arxiv_id: arXiv ID (e.g., "1706.03762")
            fields: Fields to include in response
            timeout: Request timeout in seconds

        Returns:
            Dictionary containing paper details
        """
        if not arxiv_id.strip():
            raise ValueError("arxiv_id must be provided")

        clean_id = arxiv_id.strip().split("v")[0]

        DEFAULT_FIELDS = (
            "paperId",
            "title",
            "abstract",
            "year",
            "authors",
            "venue",
            "externalIds",
            "openAccessPdf",
        )

        fields = fields or DEFAULT_FIELDS

        path = f"paper/ARXIV:{clean_id}"
        params: dict[str, Any] = {
            "fields": ",".join(fields),
        }

        resp = self.get(path=path, params=params, timeout=timeout)
        raise_for_status(resp, path=path)
        return self._parser.parse(resp, as_="json")


if __name__ == "__main__":
    client = SemanticScholarClient()

    # Example 1: General query search
    print("1. General query search:")
    result1 = client.search_papers(query="machine learning", limit=2)
    print(f"   Found {len(result1.get('data', []))} papers")

    # Example 2: Title search
    print("\n2. Title search:")
    result2 = client.search_papers(title="Attention Is All You Need", limit=2)
    print(f"   Found {len(result2.get('data', []))} papers")
    if result2.get("data"):
        print(f"   First result: {result2['data'][0].get('title')}")

    # Example 3: Author search
    print("\n3. Author search:")
    result3 = client.search_papers(author="Vaswani", limit=2)
    print(f"   Found {len(result3.get('data', []))} papers")

    # Example 4: Title + Author search
    print("\n4. Title + Author search:")
    result4 = client.search_papers(title="transformer", author="Vaswani", limit=1)
    print(f"   Found {len(result4.get('data', []))} papers")
