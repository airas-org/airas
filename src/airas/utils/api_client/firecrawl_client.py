import logging
import os
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

from airas.utils.api_client.base_http_client import BaseHTTPClient
from airas.utils.api_client.response_parser import ResponseParser

logger = getLogger(__name__)


@runtime_checkable
class ResponseParserProtocol(Protocol):
    def parse(self, response: requests.Response, *, as_: str) -> Any: ...

class FireCrawlClientError(RuntimeError): ...
class FireCrawlClientRetryableError(FireCrawlClientError): ...
class FireCrawlClientFatalError(FireCrawlClientError): ...

DEFAULT_MAX_RETRIES = 10
WAIT_POLICY = wait_exponential(multiplier=1.0, max=180.0)
RETRY_EXC = (
    FireCrawlClientRetryableError,
    ConnectionError,
    HTTPError,
    Timeout,
    RequestException,
)

FIRECRAWL_RETRY = retry(
    stop=stop_after_attempt(DEFAULT_MAX_RETRIES),
    wait=WAIT_POLICY,
    before=before_log(logger, logging.WARNING),
    before_sleep=before_sleep_log(logger, logging.WARNING),
    reraise=True,
    retry=retry_if_exception_type(RETRY_EXC), 
)


class FireCrawlClient(BaseHTTPClient):
    def __init__(
        self,
        base_url: str = "https://api.firecrawl.dev/v1",
        default_headers: dict[str, str] | None = None,
        parser: ResponseParserProtocol | None = None, 
    ):
        api_key = os.getenv("FIRE_CRAWL_API_KEY")
        if not api_key:
            raise EnvironmentError("FIRE_CRAWL_API_KEY is not set")

        auth_headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }
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
        if code == 408:
            raise FireCrawlClientRetryableError(f"Timeout (408) on {path}")
        if 500 <= code < 600:
            raise FireCrawlClientRetryableError(f"Server error {code}: {path}")
        raise FireCrawlClientFatalError(f"Client error {code}: {path}")


    @FIRECRAWL_RETRY
    def scrape(
        self,
        url: str,
        *,
        formats: list[str] | None = None,
        only_main_content: bool = True,
        wait_for: int = 5_000,
        timeout_ms: int = 15_000,
        timeout: float = 60.0,
    ) -> dict[str, str]:
        formats = formats or ["markdown"]
        payload = {
            "url": url,
            "formats": formats,
            "onlyMainContent": only_main_content,
            "waitFor": wait_for,
            "timeout": timeout_ms,
        }
        response = self.post(path="scrape", json=payload, timeout=timeout)
        self._raise_for_status(response, path="scrape")

        return self._parser.parse(response, as_="json")
