import logging
import os
from logging import getLogger
from typing import Any, Protocol, runtime_checkable

import requests  # type: ignore
from requests.exceptions import (  # type: ignore
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

from airas.utils.api_client.base_http_client import BaseHTTPClient
from airas.utils.api_client.response_parser import ResponseParser

logger = getLogger(__name__)


@runtime_checkable
class ResponseParserProtocol(Protocol):
    def parse(self, response: requests.Response, *, as_: str) -> Any: ...

class OpenAlexClientError(RuntimeError): ...
class OpenAlexClientRetryableError(OpenAlexClientError): ...
class OpenAlexClientFatalError(OpenAlexClientError): ...


_DEFAULT_MAX_RETRIES = 10
_WAIT_POLICY = wait_exponential(multiplier=1.0, max=180.0)

_RETRY_EXC = (
    OpenAlexClientRetryableError,
    ConnectionError,
    HTTPError,
    Timeout,
    RequestException,
)

OPENALEX_RETRY = retry(
    stop=stop_after_attempt(_DEFAULT_MAX_RETRIES),
    wait=_WAIT_POLICY,
    before=before_log(logger, logging.WARNING),
    before_sleep=before_sleep_log(logger, logging.WARNING),
    retry=retry_if_exception_type(_RETRY_EXC),
    reraise=True,
)


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

    @staticmethod
    def _raise_for_status(resp: requests.Response, path: str) -> None:
        code = resp.status_code
        if 200 <= code < 300:
            return
        if code in (408, 429) or 500 <= code < 600:
            raise OpenAlexClientRetryableError(f"HTTP {code}: {path}")
        raise OpenAlexClientFatalError(f"HTTP {code}: {path}")

    @OPENALEX_RETRY
    def search_papers(
        self,
        query: str,
        *,
        year: str | None = None,
        per_page: int = 20,
        page: int = 1,
        sort: str | None = "relevance_score:desc", 
        fields: tuple[str, ...] | None = None,
        timeout: float = 30.0,
    ) -> dict[str, Any]:
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
        )

        fields = fields or DEFAULT_FIELDS
        per_page = max(1, min(per_page, 200))

        params: dict[str, Any] = {
            "page": page,
            "per-page": per_page,
            "select": ",".join(fields),
            "filter": ",".join(
                ["default.search:" + query, *self._build_year_filters(year)]
            ),
        }
        if sort:
            params["sort"] = sort
        if self._key_qs:
            params["api_key"] = os.getenv("OPENALEX_API_KEY")

        path = "works"
        resp = self.get(path=path, params=params, timeout=timeout)
        self._raise_for_status(resp, path)
        return self._parser.parse(resp, as_="json")

if __name__ == "__main__":
    results = OpenAlexClient().search_papers(
        query="cnn",
        year="2020-2025", 
    )
    print(f"{results}")