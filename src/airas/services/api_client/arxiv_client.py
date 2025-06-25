import logging
from logging import getLogger
from typing import Any, Protocol, runtime_checkable

import requests
from requests.exceptions import ConnectionError, HTTPError, RequestException, Timeout
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


class ArxivClientError(RuntimeError): ...


class ArxivClientRetryableError(ArxivClientError): ...


class ArxivClientFatalError(ArxivClientError): ...


DEFAULT_MAX_RETRIES = 10
WAIT_POLICY = wait_exponential(multiplier=1.0, max=180.0)
RETRY_EXC = (
    ArxivClientRetryableError,
    ConnectionError,
    HTTPError,
    Timeout,
    RequestException,
)

ARXIV_RETRY = retry(
    stop=stop_after_attempt(DEFAULT_MAX_RETRIES),
    wait=WAIT_POLICY,
    before=before_log(logger, logging.WARNING),
    before_sleep=before_sleep_log(logger, logging.WARNING),
    reraise=True,
    retry=retry_if_exception_type(RETRY_EXC),
)


class ArxivClient(BaseHTTPClient):
    def __init__(
        self,
        base_url: str = "https://export.arxiv.org/api",
        default_headers: dict[str, str] | None = None,
        parser: ResponseParserProtocol | None = None,
    ):
        super().__init__(base_url=base_url, default_headers=default_headers)
        self._parser = parser or ResponseParser()

    @staticmethod
    def _raise_for_status(resp: requests.Response, path: str) -> None:
        code = resp.status_code
        if 200 <= code < 300:
            return

        if 500 <= code < 600:
            raise ArxivClientRetryableError(f"Server error {code} : {path}")

        raise ArxivClientFatalError(f"Client error {code} : {path}")

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
        self._raise_for_status(response, path="query")

        return self._parser.parse(response, as_="xml")

    @ARXIV_RETRY
    def fetch_pdf(self, arxiv_id: str, timeout: float = 30.0) -> requests.Response:
        pdf_url = f"https://arxiv.org/pdf/{arxiv_id}.pdf"

        response = requests.get(pdf_url, stream=True, timeout=timeout)
        match response.status_code:
            case 200:
                return response
            case 404:
                logger.error(f"PDF not found (404): {pdf_url}")
                raise ArxivClientFatalError(f"PDF not found: {arxiv_id}")
            case _:
                self._raise_for_status(response, f"fetch_pdf {arxiv_id}")
                return response
