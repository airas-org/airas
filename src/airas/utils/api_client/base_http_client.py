import httpx
import requests
import logging
from abc import ABC
from airas.utils.api_client.parser_mixin import ResponseParserMixIn

logger = logging.getLogger(__name__)


class BaseHTTPClient(ResponseParserMixIn, ABC):
    def __init__(
        self,
        base_url: str,
        default_headers: dict[str, str] | None = None,
    ):
        self.base_url = base_url.rstrip("/")
        self.default_headers = default_headers or {}
        self.session = requests.Session()

    def _send(
        self,
        method: str,
        path: str,
        *,
        headers: dict[str, str] | None = None,
        params: dict | None = None,
        json: dict | None = None,
        stream: bool = False,
        timeout: float = 10.0,
    ) -> requests.Response:
        url = f"{self.base_url}/{path.lstrip('/')}"
        hdrs = {**self.default_headers, **(headers or {})}
        resp = self.session.request(
            method=method,
            url=url,
            headers=hdrs,
            params=params,
            json=json,
            timeout=timeout,
            stream=stream,
        )
        resp.raise_for_status()
        return resp

    def request(
        self,
        method: str,
        path: str,
        *,
        headers: dict[str, str] | None = None,
        params: dict | None = None,
        json: dict | None = None,
        stream: bool = False,
        timeout: float = 10.0,
    ) -> dict | str | bytes | None:
        try:
            resp = self._send(
                method.upper(),
                path,
                headers=headers,
                params=params,
                json=json,
                stream=stream,
                timeout=timeout,
            )
            return self._parse_response(resp)
        except Exception as e:
            logger.warning(f"Error during API request: {e}")
            return None  # TODO


class AsyncBaseHTTPClient(ResponseParserMixIn, ABC):
    def __init__(self, base_url: str, default_headers: dict[str, str] | None = None):
        self.base_url = base_url.rstrip("/")
        self.default_headers = default_headers or {}
        self.session = httpx.AsyncClient()

    async def _send(): ...

    async def request(): ...
