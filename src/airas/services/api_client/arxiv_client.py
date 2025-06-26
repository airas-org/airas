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
    def search(
        self,
        *,
        query: str,
        start: int = 0,
        max_results: int = 10,
        sort_by: str = "relevance",
        sort_order: str = "descending",
        from_date: str | None = None,
        to_date: str | None = None,
        timeout: float = 15.0,
    ) -> str:
        sanitized = query.replace(":", "")
        if from_date and to_date:
            search_q = f"(all:{sanitized}) AND submittedDate:[{from_date} TO {to_date}]"
        else:
            search_q = f"all:{sanitized}"

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
    def fetch_pdf(self, arxiv_id: str, timeout: float = 30.0) -> requests.Response:
        pdf_url = f"https://arxiv.org/pdf/{arxiv_id}.pdf"

        response = requests.get(pdf_url, stream=True, timeout=timeout)
        raise_for_status(response, f"fetch_pdf {arxiv_id}")
        return response
