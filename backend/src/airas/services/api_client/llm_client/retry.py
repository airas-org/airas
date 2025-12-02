import json
import logging
from logging import getLogger

import httpx
from google.genai import errors as genai_errors
from pydantic import ValidationError
from tenacity import (
    before_log,
    before_sleep_log,
    retry,
    retry_if_exception,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

logger = getLogger(__name__)

DEFAULT_MAX_RETRIES = 50
WAIT_POLICY = wait_exponential(multiplier=1.0, max=600.0)

RETRY_EXC = (
    httpx.ConnectError,
    httpx.HTTPStatusError,
    httpx.TimeoutException,
    httpx.HTTPError,
    genai_errors.APIError,
    json.JSONDecodeError,
    ValidationError,
)


def _is_transient(e: BaseException) -> bool:
    # HTTPStatusError from httpx
    if isinstance(e, httpx.HTTPStatusError):
        return e.response.status_code in (429, 500, 502, 503, 504)
    # Network-related errors are retryable
    if isinstance(e, (httpx.ConnectError, httpx.TimeoutException, httpx.HTTPError)):
        return True
    # Check if error message contains transient failure keywords (basic support for Google SDK)
    msg = str(e).upper()
    return any(
        k in msg
        for k in (
            "RESOURCE_EXHAUSTED",
            "RATE_LIMIT",
            "UNAVAILABLE",
            "DEADLINE_EXCEEDED",
        )
    )


_fallback_wait = wait_exponential(multiplier=1.0, max=180.0)


def wait_server_hint_or_exponential(retry_state) -> float:
    e = retry_state.outcome.exception() if retry_state.outcome else None
    if e is not None:
        # HTTP header Retry-After (basic support for numeric seconds only)
        resp = getattr(e, "response", None)
        if resp is not None:
            ra = resp.headers.get("Retry-After")
            if ra and ra.isdigit():
                return float(ra)

        # Google's RetryInfo (basic support for "29s" format only)
        # Assumes payload is in exception's response.json() or args[0]
        payload = None
        if resp is not None:
            try:
                payload = resp.json()
            except Exception:
                pass
        if payload is None and e.args and isinstance(e.args[0], dict):
            payload = e.args[0]

        try:
            details = (payload or {}).get("error", {}).get("details", []) or (
                payload or {}
            ).get("details", [])
            for d in details:
                if isinstance(d, dict) and d.get("@type", "").endswith(
                    "google.rpc.RetryInfo"
                ):
                    rd = d.get("retryDelay")  # Example: "29s"
                    if isinstance(rd, str) and rd.endswith("s"):
                        return float(rd[:-1])  # "29s" -> 29.0
        except Exception:
            pass

    # Fall back to exponential backoff if no hints
    return _fallback_wait(retry_state)


LLM_RETRY = retry(
    # Combination of existing type-based checks + simple function for transient failures only
    retry=retry_if_exception_type(RETRY_EXC) | retry_if_exception(_is_transient),
    stop=stop_after_attempt(DEFAULT_MAX_RETRIES),
    wait=wait_server_hint_or_exponential,
    before=before_log(logger, logging.INFO),
    before_sleep=before_sleep_log(logger, logging.WARNING),
    reraise=True,
)
