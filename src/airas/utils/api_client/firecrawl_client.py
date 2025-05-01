import os
import logging
from logging import getLogger
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
    before_log,
    before_sleep_log,
)
from requests.exceptions import HTTPError, ConnectionError, Timeout, RequestException
from airas.utils.api_client.base_http_client import BaseHTTPClient

logger = getLogger(__name__)
FIRE_CRAWL_API_KEY = os.getenv("FIRE_CRAWL_API_KEY")

RETRY_EXC = (HTTPError, ConnectionError, Timeout, RequestException, Exception)
MAX_RETRIES = 10
WAIT_POLICY = wait_exponential(multiplier=1.0, max=180.0)


class FireCrawlClient(BaseHTTPClient):
    def __init__(
        self,
        base_url: str = "https://api.firecrawl.dev/v1",
        default_headers: dict[str, str] | None = None,
    ):
        if not FIRE_CRAWL_API_KEY:
            raise EnvironmentError("FIRE_CRAWL_API_KEY is not set")
        auth_headers = {
            "Authorization": f"Bearer {FIRE_CRAWL_API_KEY}",
            "Content-Type": "application/json",
        }
        super().__init__(
            base_url=base_url,
            default_headers={**auth_headers, **(default_headers or {})},
        )

    @retry(
        retry=retry_if_exception_type(RETRY_EXC),
        stop=stop_after_attempt(MAX_RETRIES),
        wait=WAIT_POLICY,
        before=before_log(logger, logging.WARNING),
        before_sleep=before_sleep_log(logger, logging.WARNING),
        reraise=True,
    )
    def scrape(
        self,
        url: str,
        *,
        formats: list[str] = ["markdown"],
        only_main_content: bool = True,
        wait_for: int = 5000,
        timeout_ms: int = 15000,
        timeout: float = 60.0,
    ) -> dict | str | bytes | None:
        payload = {
            "url": url,
            "formats": formats,
            "onlyMainContent": only_main_content,
            "waitFor": wait_for,
            "timeout": timeout_ms,
        }
        return self.request("POST", "scrape", json=payload, timeout=timeout)
