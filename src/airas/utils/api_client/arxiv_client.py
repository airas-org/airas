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

RETRY_EXC = (HTTPError, ConnectionError, Timeout, RequestException, Exception)
MAX_RETRIES = 10
WAIT_POLICY = wait_exponential(multiplier=1.0, max=180.0)


class ArxivClient(BaseHTTPClient):
    def __init__(
        self,
        base_url: str = "https://export.arxiv.org/api",
        default_headers: dict[str, str] | None = None,
        # max_retries: int = 10,
        # initial_wait: float = 1.0,
        # max_wait: float = 180.0,
    ):
        super().__init__(base_url=base_url, default_headers=default_headers)
        # self.max_retries=max_retries
        # self.initial_wait=initial_wait
        # self.max_wait=max_wait

    # TODO: インスタンス変数を反映したい場合、`Retrying`を使う
    @retry(
        retry=retry_if_exception_type(RETRY_EXC),
        stop=stop_after_attempt(MAX_RETRIES),
        wait=WAIT_POLICY,
        before=before_log(logger, logging.WARNING),
        before_sleep=before_sleep_log(logger, logging.WARNING),
        reraise=True,
    )
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
    ) -> dict | str | bytes | None:
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
        return self.request("GET", "query", params=params, timeout=timeout)
