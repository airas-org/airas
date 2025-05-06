import logging
from abc import ABC
from typing import Literal, overload

import httpx
import requests

from airas.utils.api_client.parser_mixin import ResponseParserMixIn

logger = logging.getLogger(__name__)


class BaseHTTPClient(ResponseParserMixIn, ABC):
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

    @overload
    def get(
        self, path: str, *, parse: Literal[True], **kwargs
    ) -> dict | bytes | str: ...
    @overload
    def get(
        self, path: str, *, parse: Literal[False], **kwargs
    ) -> requests.Response: ...

    def get(self, path: str, **kwargs):
        return self._request("GET", path, **kwargs)

    @overload
    def post(
        self, path: str, *, parse: Literal[True], **kwargs
    ) -> dict | bytes | str: ...
    @overload
    def post(
        self, path: str, *, parse: Literal[False], **kwargs
    ) -> requests.Response: ...

    def post(self, path: str, **kwargs):
        return self._request("POST", path, **kwargs)
    
    @overload
    def put(
        self, path: str, *, parse: Literal[True], **kwargs
    ) -> dict | bytes | str: ...
    @overload
    def put(
        self, path: str, *, parse: Literal[False], **kwargs
    ) -> requests.Response: ...

    def put(self, path: str, **kwargs):
        return self._request("PUT", path, **kwargs)

    def _request(
        self,
        method: str,
        path: str,
        *,
        headers: dict[str, str] | None = None,
        params: dict | None = None,
        json: dict | None = None,
        stream: bool = False,
        timeout: float = 10.0,
        parse: bool = True,
    ) -> dict | str | bytes | requests.Response | None:
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
            if parse:
                return self._parse_response(response)
            return response
        except Exception as e:
            logger.warning(f"[{self.__class__.__name__}] {method} {url}: {e}")
            raise


class AsyncBaseHTTPClient(ResponseParserMixIn, ABC):
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

    @overload
    async def get(
        self, path: str, *, parse: Literal[True], **kwargs
    ) -> dict | bytes | str: ...
    @overload
    async def get(
        self, path: str, *, parse: Literal[False], **kwargs
    ) -> requests.Response: ...

    async def get(self, path: str, **kwargs):
        return await self._request("GET", path, **kwargs)

    @overload
    async def post(
        self, path: str, *, parse: Literal[True], **kwargs
    ) -> dict | bytes | str: ...
    @overload
    async def post(
        self, path: str, *, parse: Literal[False], **kwargs
    ) -> requests.Response: ...
    async def post(self, path: str, **kwargs):
        return await self._request("POST", path, **kwargs)

    async def _request(
        self,
        method: str,
        path: str,
        *,
        headers: dict[str, str] | None = None,
        params: dict | None = None,
        json: dict | None = None,
        stream: bool = False,
        timeout: float = 10.0,
        parse: bool = True,
    ) -> dict | str | bytes | requests.Response | None:
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
            if parse:
                return self._parse_response(response)
            return response
        except Exception as e:
            logger.warning(f"[{self.__class__.__name__}] {method} {url}: {e}")
            raise
