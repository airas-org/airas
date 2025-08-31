from typing import Literal

from airas.services.api_client.llm_client.google_genai_client import (
    VERTEXAI_MODEL,
    GoogelGenAIClient,
)
from airas.services.api_client.llm_client.openai_client import (
    OPENAI_MODEL,
    OpenAIClient,
)
from airas.services.api_client.llm_client.retry import LLM_RETRY

LLM_MODEL = Literal[OPENAI_MODEL, VERTEXAI_MODEL]


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
