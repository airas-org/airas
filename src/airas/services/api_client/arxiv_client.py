from logging import getLogger
from typing import Any, Protocol, runtime_checkable

import requests

from airas.services.api_client.base_http_client import BaseHTTPClient
from airas.services.api_client.response_parser import ResponseParser
from airas.services.api_client.retry_policy import make_retry_policy, raise_for_status

logger = getLogger(__name__)

ARXIV_RETRY = make_retry_policy()


@runtime_checkable
class ResponseParserProtocol(Protocol):
    def parse(self, response: requests.Response, *, as_: str) -> Any: ...


class ArxivClient(BaseHTTPClient):
    def __init__(
        self,
        base_url: str = "https://export.arxiv.org/api",
        default_headers: dict[str, str] | None = None,
        parser: ResponseParserProtocol | None = None,
    ):
        super().__init__(base_url=base_url, default_headers=default_headers)
        self._parser = parser or ResponseParser()

    @ARXIV_RETRY
    def search_papers(
        self,
        query: str | None = None,
        *,
        title: str | None = None,
        author: str | None = None,
        start: int = 0,
        max_results: int = 10,
        sort_by: str = "relevance",
        sort_order: str = "descending",
        from_date: str | None = None,
        to_date: str | None = None,
        search_field: str = "all",
        timeout: float = 15.0,
    ) -> str:
        """
        Search papers using arXiv API with flexible search options.

        Args:
            query: Free-text search query
            title: Title-specific search (uses ti: field)
            author: Author-specific search (uses au: field)
            start: Starting index for pagination
            max_results: Maximum number of results to return
            sort_by: Sort criteria ("relevance", "lastUpdatedDate", "submittedDate")
            sort_order: Sort order ("ascending", "descending")
            from_date: Start date filter (YYYY-MM-DD format)
            to_date: End date filter (YYYY-MM-DD format)
            search_field: Field to search in for general query ("all", "ti", "au", "abs", etc.)
            timeout: Request timeout in seconds

        Returns:
            XML string response from arXiv API

        Note:
            - If title/author are provided, structured search takes precedence over general query
            - Either query OR title/author must be provided
        """

        search_parts = []
        if title or author:
            if title and title.strip():
                exact_title = f'"{title.strip()}"'
                search_parts.append(f"ti:{exact_title}")

            if author and author.strip():
                sanitized_author = author.strip().replace(":", "")
                search_parts.append(f"au:{sanitized_author}")

        elif query and query.strip():
            sanitized = query.strip().replace(":", "")
            search_parts.append(f"{search_field}:{sanitized}")
        else:
            raise ValueError("Either 'query' or 'title'/'author' must be provided")

        search_q = " AND ".join(search_parts)

        if from_date and to_date:
            search_q = f"({search_q}) AND submittedDate:[{from_date} TO {to_date}]"

        params = {
            "search_query": search_q,
            "start": start,
            "max_results": max_results,
            "sortBy": sort_by,
            "sortOrder": sort_order,
        }
        response = self.get(path="query", params=params, timeout=timeout)
        raise_for_status(response, path="query")

        return self._parser.parse(response, as_="xml")

    @ARXIV_RETRY
    def get_paper_by_id(
        self,
        arxiv_id: str,
        timeout: float = 15.0,
    ) -> str:
        """
        Get paper details by arXiv ID.

        Args:
            arxiv_id: arXiv ID (e.g., "1706.03762" or "1706.03762v1")
            timeout: Request timeout in seconds

        Returns:
            XML string response from arXiv API
        """
        if not arxiv_id.strip():
            raise ValueError("arxiv_id must be provided")

        clean_id = arxiv_id.strip().split("v")[0]

        params = {
            "id_list": clean_id,
            "max_results": 1,
        }
        response = self.get(path="query", params=params, timeout=timeout)
        raise_for_status(response, path="query")

        return self._parser.parse(response, as_="xml")


if __name__ == "__main__":
    import feedparser

    client = ArxivClient()

    # Example 1: General query search
    print("1. General query search:")
    result1 = client.search_papers(query="machine learning", max_results=2)
    feed1 = feedparser.parse(result1)
    print(f"   Found {len(feed1.entries)} papers")

    # Example 2: Title search
    print("\n2. Title search:")
    result2 = client.search_papers(title="Attention Is All You Need", max_results=2)
    feed2 = feedparser.parse(result2)
    print(f"   Found {len(feed2.entries)} papers")
    if feed2.entries:
        print(f"   First result: {feed2.entries[0].title}")

    # Example 3: Author search
    print("\n3. Author search:")
    result3 = client.search_papers(author="Vaswani", max_results=2)
    feed3 = feedparser.parse(result3)
    print(f"   Found {len(feed3.entries)} papers")

    # Example 4: Title + Author search
    print("\n4. Title + Author search:")
    result4 = client.search_papers(title="transformer", author="Vaswani", max_results=1)
    feed4 = feedparser.parse(result4)
    print(f"   Found {len(feed4.entries)} papers")
