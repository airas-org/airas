import logging
from logging import getLogger
from typing import Literal

from google.genai import errors as genai_errors
from requests.exceptions import ConnectionError, HTTPError, RequestException, Timeout
from tenacity import (
    before_log,
    before_sleep_log,
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from airas.services.api_client.llm_client.google_genai_client import (
    VERTEXAI_MODEL,
    GoogelGenAIClient,
)
from airas.services.api_client.llm_client.openai_client import (
    OPENAI_MODEL,
    OpenAIClient,
)

logger = getLogger(__name__)

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
    before=before_log(logger, logging.INFO),
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

    @LLM_RETRY
    def text_embedding(self, message: str, model_name: str = "gemini-embedding-001"):
        return self.client.text_embedding(message=message, model_name=model_name)

    @LLM_RETRY
    def web_search(self, message: str):
        """
        Perform web search using OpenAI API (only available for OpenAI models).

        Args:
            message: The search prompt

        Returns:
            Tuple of (response_text, cost)
        """
        if not hasattr(self.client, "web_search"):
            raise ValueError(f"Web search not supported for {self.llm_name}")
        return self.client.web_search(model_name=self.llm_name, message=message)
