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
        sync_session: requests.Session | None = None,
        async_session: httpx.AsyncClient | None = None,
    ):
        self.base_url = base_url.rstrip("/")
        self.default_headers = default_headers or {}
        self.sync_session = sync_session or requests.Session()
        self.async_session = async_session or httpx.AsyncClient(follow_redirects=True)

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
        full_url: str | None = None,
    ) -> requests.Response:
        """Synchronous HTTP request."""
        if full_url:
            url = full_url
        else:
            url = f"{self.base_url}/{path.lstrip('/')}"
        headers = {**self.default_headers, **(headers or {})}

        try:
            response = self.sync_session.request(
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

    async def arequest(
        self,
        method: str,
        path: str,
        *,
        headers: dict[str, str] | None = None,
        params: dict | None = None,
        json: dict | None = None,
        timeout: float = 10.0,
        full_url: str | None = None,
    ) -> httpx.Response:
        """Asynchronous HTTP request."""
        if full_url:
            url = full_url
        else:
            url = f"{self.base_url}/{path.lstrip('/')}"
        headers = {**self.default_headers, **(headers or {})}

        try:
            response = await self.async_session.request(
                method=method.upper(),
                url=url,
                headers=headers,
                params=params,
                json=json,
                timeout=timeout,
            )
            return response
        except Exception as e:
            logger.warning(f"[{self.__class__.__name__}] {method} {url}: {e}")
            raise

    # Synchronous methods
    def get(self, path: str, **kwargs) -> requests.Response:
        return self.request("GET", path, **kwargs)

    def post(self, path: str, **kwargs) -> requests.Response:
        return self.request("POST", path, **kwargs)

    def put(self, path: str, **kwargs) -> requests.Response:
        return self.request("PUT", path, **kwargs)

    def patch(self, path: str, **kwargs) -> requests.Response:
        return self.request("PATCH", path, **kwargs)

    # Asynchronous methods
    async def aget(self, path: str, **kwargs) -> httpx.Response:
        return await self.arequest("GET", path, **kwargs)

    async def apost(self, path: str, **kwargs) -> httpx.Response:
        return await self.arequest("POST", path, **kwargs)

    async def aput(self, path: str, **kwargs) -> httpx.Response:
        return await self.arequest("PUT", path, **kwargs)

    async def apatch(self, path: str, **kwargs) -> httpx.Response:
        return await self.arequest("PATCH", path, **kwargs)
