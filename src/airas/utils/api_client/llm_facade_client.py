import requests
from typing import Literal
from tenacity import retry, stop_after_attempt, wait_fixed, retry_if_exception_type
from airas.utils.api_client.openai_client import OpenAIClient, OPENAI_MODEL
from airas.utils.api_client.google_genai_client import GoogelGenAIClient, VERTEXAI_MODEL


LLM_MODEL = Literal[OPENAI_MODEL, VERTEXAI_MODEL]

LLM_RETRY = retry(
    retry=retry_if_exception_type(requests.exceptions.ConnectionError),
    stop=stop_after_attempt(3),
    wait=wait_fixed(1),
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
