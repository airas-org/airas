import logging
from logging import getLogger

from requests.exceptions import ConnectionError, HTTPError, RequestException, Timeout
from tenacity import (
    before_log,
    before_sleep_log,
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)
from tenacity.wait import wait_base as WaitBase

from airas.services.api_client.response_parser import Response


class HTTPClientError(RuntimeError): ...


class HTTPClientRetryableError(HTTPClientError): ...


class HTTPClientFatalError(HTTPClientError): ...


_LOGGER = getLogger(__name__)
_DEFAULT_MAX_RETRIES = 10
_DEFAULT_WAIT = wait_exponential(multiplier=1.0, max=180.0)
_DEFAULT_EXC: tuple[type[BaseException], ...] = (
    HTTPClientRetryableError,
    ConnectionError,
    HTTPError,
    Timeout,
    RequestException,
)


# TODO: When implementing POST requests, consider idempotency concerns.
def make_retry_policy(
    max_retries: int = _DEFAULT_MAX_RETRIES,
    wait: WaitBase = _DEFAULT_WAIT,
    retryable_exc: tuple[type[BaseException], ...] = _DEFAULT_EXC,
):
    return retry(
        stop=stop_after_attempt(max_retries),
        wait=wait,
        retry=retry_if_exception_type(retryable_exc),
        before=before_log(_LOGGER, logging.INFO),
        before_sleep=before_sleep_log(_LOGGER, logging.WARNING),
        reraise=True,
    )


def raise_for_status(response: Response, *, path: str = "") -> None:
    code = response.status_code
    if 200 <= code < 300:
        return
    if code in (408, 429) or 500 <= code < 600:
        raise HTTPClientRetryableError(f"{code} on {path}: {response.text}")
    raise HTTPClientFatalError(f"{code} on {path}: {response.text}")
