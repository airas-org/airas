"""
Semantic Scholar Graph API クライアント
参考: https://api.semanticscholar.org/api-docs/graph :contentReference[oaicite:0]{index=0}
"""

from __future__ import annotations

import logging
import os
from logging import getLogger
from typing import Any, Protocol, runtime_checkable

import requests
from requests.exceptions import (
    ConnectionError,
    HTTPError,
    RequestException,
    Timeout,
)
from tenacity import (
    before_log,
    before_sleep_log,
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from airas.services.api_client.base_http_client import BaseHTTPClient
from airas.services.api_client.response_parser import ResponseParser

logger = getLogger(__name__)


@runtime_checkable
class ResponseParserProtocol(Protocol):
    def parse(self, response: requests.Response, *, as_: str) -> Any: ...

class SemanticScholarClientError(RuntimeError): ...
class SemanticScholarClientRetryableError(SemanticScholarClientError): ...
class SemanticScholarClientFatalError(SemanticScholarClientError): ...

_DEFAULT_MAX_RETRIES = 10
_WAIT_POLICY = wait_exponential(multiplier=1.0, max=180.0)

_RETRY_EXC = (
    SemanticScholarClientRetryableError,
    ConnectionError,
    HTTPError,
    Timeout,
    RequestException,
)

SEMANTIC_SCHOLAR_RETRY = retry(
    stop=stop_after_attempt(_DEFAULT_MAX_RETRIES),
    wait=_WAIT_POLICY,
    before=before_log(logger, logging.WARNING),
    before_sleep=before_sleep_log(logger, logging.WARNING),
    retry=retry_if_exception_type(_RETRY_EXC),
    reraise=True,
)


class SemanticScholarClient(BaseHTTPClient):
    def __init__(
        self,
        *,
        base_url: str = "https://api.semanticscholar.org/graph/v1",
        default_headers: dict[str, str] | None = None,
        parser: ResponseParserProtocol | None = None,
    ):
        api_key: str | None = os.getenv("SEMANTIC_SCHOLAR_API_KEY")
        if not api_key:
            raise EnvironmentError("SEMANTIC_SCHOLAR_API_KEY is not set")

        auth_headers = {"x-api-key": api_key}

        super().__init__(
            base_url=base_url,
            default_headers={**auth_headers, **(default_headers or {})},
        )
        self._parser = parser or ResponseParser()

    @staticmethod
    def _raise_for_status(resp: requests.Response, path: str) -> None:
        code = resp.status_code
        if 200 <= code < 300:
            return
        if code in (408, 429) or 500 <= code < 600:
            raise SemanticScholarClientRetryableError(f"HTTP {code}: {path}")
        raise SemanticScholarClientFatalError(f"HTTP {code}: {path}")


    @SEMANTIC_SCHOLAR_RETRY
    def search_paper_titles(
        self,
        query: str,
        *,
        fields: list[str] | None = None,
        year: str | None = None,
        publication_date_or_year: str | None = None,
        limit: int = 20,
        offset: int = 0,
        timeout: float = 30.0,
    ) -> dict[str, Any]:
        # https://api.semanticscholar.org/api-docs/graph#tag/Paper-Data/operation/get_graph_paper_title_search

        base_fields = ["title"]
        if fields:
            base_fields.extend(fields)
        params: dict[str, Any] = {
            "query": query,
            "fields": ",".join(dict.fromkeys(base_fields)), 
            "limit": limit,
            "offset": offset,
        }
        if year:
            params["year"] = year
        if publication_date_or_year:
            params["publicationDateOrYear"] = publication_date_or_year

        path = "paper/search"
        response = self.get(path=path, params=params, timeout=timeout)
        match response.status_code:
            case 200:
                logger.info("Best Title match paper with default or requested fields (200).")
                return self._parser.parse(response, as_="json")
            case 400:
                logger.error("Bad query parameters (404).")
                raise SemanticScholarClientFatalError
            case 404:
                logger.error("No title match (404).")
                raise SemanticScholarClientFatalError
            case _:
                self._raise_for_status(response, path)
                raise SemanticScholarClientFatalError
