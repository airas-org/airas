import logging
from typing import Any, Literal, overload

import requests

logger = logging.getLogger(__name__)


class UnexpectedContentTypeError(RuntimeError): ...


class ResponseParser:
    @overload
    def parse(self, response: requests.Response, *, as_: Literal["json"]) -> dict: ...
    @overload
    def parse(
        self, response: requests.Response, *, as_: Literal["text", "xml"]
    ) -> str: ...
    @overload
    def parse(
        self, response: requests.Response, *, as_: Literal["bytes", "binary", "raw"]
    ) -> bytes: ...
    @overload
    def parse(self, response: requests.Response, *, as_: Literal["none"]) -> None: ...

    def parse(self, response: requests.Response, *, as_: str = "json") -> Any:
        fmt = as_.lower()
        if fmt == "json":
            return self._to_json(response)
        if fmt == "text":
            return self._to_text(response)
        if fmt in {"bytes", "binary", "xml", "raw"}:
            return self._to_bytes(response)
        if fmt == "none":
            return self._to_none(response)

        raise ValueError(f"Unsupported 'as_' parameter: {as_!r}")

    def _to_json(self, response: requests.Response) -> dict:
        if "application/json" not in response.headers.get("Content-Type", ""):
            raise UnexpectedContentTypeError("Expected JSON response")
        return response.json() if response.text.strip() else {}

    def _to_text(self, response: requests.Response) -> str:
        if "text/" not in response.headers.get("Content-Type", ""):
            raise UnexpectedContentTypeError("Expected text response")
        return response.text.strip()

    def _to_bytes(self, response: requests.Response) -> bytes:
        return response.content

    def _to_none(self, response: requests.Response) -> None:
        return None
