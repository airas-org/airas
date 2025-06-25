import logging

import httpx
import requests

logger = logging.getLogger(__name__)


class BaseHTTPClient:
    def __init__(
        self,
        base_url: str,
        *,
        default_headers: dict[str, str] | None = None,
        session: requests.Session | None = None,
    ):
        self.base_url = base_url.rstrip("/")
        self.default_headers = default_headers or {}
        self.session = session or requests.Session()

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
    ) -> requests.Response:
        url = f"{self.base_url}/{path.lstrip('/')}"
        headers = {**self.default_headers, **(headers or {})}

        try:
            response = self.session.request(
                method=method.upper(),
                url=url,
                headers=headers,
                params=params,
                json=json,
                stream=stream,
                timeout=timeout,
            )
            return response
        except Exception as e:
            logger.warning(f"[{self.__class__.__name__}] {method} {url}: {e}")
            raise

    def get(self, path: str, **kwargs) -> requests.Response:
        return self.request("GET", path, **kwargs)

    def post(self, path: str, **kwargs) -> requests.Response:
        return self.request("POST", path, **kwargs)

    def put(self, path: str, **kwargs) -> requests.Response:
        return self.request("PUT", path, **kwargs)


class AsyncBaseHTTPClient:
    def __init__(
        self,
        base_url: str,
        *,
        default_headers: dict[str, str] | None = None,
        session: httpx.AsyncClient | None = None,
    ):
        self.base_url = base_url.rstrip("/")
        self.default_headers = default_headers or {}
        self.session = session or httpx.AsyncClient()

    async def request(
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
        headers = {**self.default_headers, **(headers or {})}

        try:
            response = await self.session.request(
                method=method.upper(),
                url=url,
                headers=headers,
                params=params,
                json=json,
                stream=stream,
                timeout=timeout,
            )
            return response
        except Exception as e:
            logger.warning(f"[{self.__class__.__name__}] {method} {url}: {e}")
            raise

    async def get(self, path: str, **kwargs) -> requests.Response:
        return self.request("GET", path, **kwargs)

    async def post(self, path: str, **kwargs) -> requests.Response:
        return self.request("POST", path, **kwargs)

    async def put(self, path: str, **kwargs) -> requests.Response:
        return self.request("PUT", path, **kwargs)
