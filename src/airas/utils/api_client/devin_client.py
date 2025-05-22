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


class DevinClientError(RuntimeError): ...
class DevinClientRetryableError(DevinClientError): ...
class DevinClientFatalError(DevinClientError): ...


DEFAULT_MAX_RETRIES = 10
WAIT_POLICY = wait_exponential(multiplier=1.0, max=180.0)
RETRY_EXC = (
    DevinClientRetryableError,
    ConnectionError,
    HTTPError,
    Timeout,
    RequestException,
)

DEVIN_RETRY = retry(
    stop=stop_after_attempt(DEFAULT_MAX_RETRIES),
    wait=WAIT_POLICY,
    before=before_log(logger, logging.WARNING),
    before_sleep=before_sleep_log(logger, logging.WARNING),
    reraise=True,
    retry=retry_if_exception_type(RETRY_EXC),
)


class DevinClient(BaseHTTPClient):
    def __init__(
        self,
        base_url: str = "https://api.devin.ai/v1",
        default_headers: dict[str, str] | None = None,
        parser: ResponseParserProtocol | None = None,
    ):
        api_key = os.getenv("DEVIN_API_KEY")
        if not api_key:
            raise EnvironmentError("DEVIN_API_KEY is not set")

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
        if code == (408, 429):
            raise DevinClientRetryableError(f"Retryable error {code} on {path}")
        if 500 <= code < 600:
            raise DevinClientRetryableError(f"Server error {code}: {path}")
        raise DevinClientFatalError(f"Client error {code}: {path}")


    @DEVIN_RETRY
    def create_session(
        self,
        *,
        prompt_template,
        idempotent: bool = True,
        timeout: float = 60.0,
    ) -> dict[str, Any]:
        # https://docs.devin.ai/api-reference/sessions/create-a-new-devin-session

        payload = {
            "prompt": prompt_template,
            "idempotent": idempotent,
        }

        response = self.post(path="sessions", json=payload, timeout=timeout)
        self._raise_for_status(response, path="sessions")

        return self._parser.parse(response, as_="json")


    @DEVIN_RETRY
    def retrieve_session(
        self,
        session_id: str,
        *,
        timeout: float = 60.0,
    ) -> dict[str, Any]:
        # https://docs.devin.ai/api-reference/sessions/retrieve-details-about-an-existing-session
        path = f"session/{session_id}"
        response = self.get(path=path, timeout=timeout)
        self._raise_for_status(response, path)
        return self._parser.parse(response, as_="json")


    @DEVIN_RETRY
    def send_message(
        self,
        *,
        session_id: str,
        message: str, 
        extra_params: dict[str, Any] | None = None, 
        timeout: float = 60.0,
    ) -> dict[str, Any]:
        # https://docs.devin.ai/api-reference/sessions/send-a-message-to-an-existing-devin-session
        path = f"session/{session_id}/message"
        payload = {
            "message": message,
            **(extra_params or {})
        }
        response = self.post(path=path, json=payload, timeout=timeout)
        self._raise_for_status(response, path)
        return self._parser.parse(response, as_="json")