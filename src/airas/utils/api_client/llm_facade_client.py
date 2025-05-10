import logging
from logging import getLogger
from typing import Literal

from requests.exceptions import ConnectionError, HTTPError, RequestException, Timeout
from tenacity import (
    before_log,
    before_sleep_log,
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

logger = getLogger(__name__)
from google.genai import errors as genai_errors

from airas.utils.api_client.google_genai_client import VERTEXAI_MODEL, GoogelGenAIClient
from airas.utils.api_client.openai_client import OPENAI_MODEL, OpenAIClient

LLM_MODEL = Literal[OPENAI_MODEL, VERTEXAI_MODEL]
DEFAULT_MAX_RETRIES = 10
WAIT_POLICY = wait_exponential(multiplier=1.0, max=180.0)

RETRY_EXC = (
    ConnectionError,
    HTTPError,
    Timeout,
    RequestException,
    genai_errors.APIError, 
)

LLM_RETRY = retry(
    retry=retry_if_exception_type(RETRY_EXC),
    stop=stop_after_attempt(DEFAULT_MAX_RETRIES),
    wait=WAIT_POLICY,
    before=before_log(logger, logging.WARNING),
    before_sleep=before_sleep_log(logger, logging.WARNING),
    reraise=True,
)


class LLMFacadeClient:
    def __init__(self, llm_name: LLM_MODEL):
        self.llm_name = llm_name
        if llm_name in OPENAI_MODEL.__args__:
            self.client = OpenAIClient()
        elif llm_name in VERTEXAI_MODEL.__args__:
            self.client = GoogelGenAIClient()
        else:
            raise ValueError(f"Unsupported LLM model: {llm_name}")

    @LLM_RETRY
    def generate(self, message: str):
        return self.client.generate(model_name=self.llm_name, message=message)

    @LLM_RETRY
    def structured_outputs(self, message: str, data_model):
        return self.client.structured_outputs(
            model_name=self.llm_name, message=message, data_model=data_model
        )
