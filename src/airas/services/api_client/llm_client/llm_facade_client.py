from typing import Literal, Optional

from airas.services.api_client.llm_client.anthropic_client import (
    CLAUDE_MODEL,
    AnthropicClient,
)
from airas.services.api_client.llm_client.google_genai_client import (
    VERTEXAI_MODEL,
    GoogleGenAIClient,
)
from airas.services.api_client.llm_client.openai_client import (
    OPENAI_MODEL,
    OpenAIClient,
)
from airas.services.api_client.llm_client.retry import LLM_RETRY

LLM_MODEL = Literal[OPENAI_MODEL, VERTEXAI_MODEL, CLAUDE_MODEL]


class LLMFacadeClient:
    def __init__(
        self,
        llm_name: LLM_MODEL,
        openai_client: Optional[OpenAIClient] = None,
        anthropic_client: Optional[AnthropicClient] = None,
        google_genai_client: Optional[GoogleGenAIClient] = None,
    ):
        self.llm_name = llm_name
        # For backward compatibility: A new client instance is automatically created if called without arguments.
        if llm_name in OPENAI_MODEL.__args__:
            self.client = openai_client or OpenAIClient()
        elif llm_name in VERTEXAI_MODEL.__args__:
            self.client = google_genai_client or GoogleGenAIClient()
        elif llm_name in CLAUDE_MODEL.__args__:
            self.client = anthropic_client or AnthropicClient()
        else:
            raise ValueError(f"Unsupported LLM model: {llm_name}")

    @LLM_RETRY
    def generate(self, message: str):
        return self.client.generate(model_name=self.llm_name, message=message)

    @LLM_RETRY
    def structured_outputs(self, message: str, data_model):
        # NOTE:The Anthropic model does not support structured output.
        if self.llm_name in CLAUDE_MODEL.__args__:
            raise NotImplementedError(
                "Structured output is not supported for Anthropic models."
            )
        return self.client.structured_outputs(
            model_name=self.llm_name, message=message, data_model=data_model
        )

    @LLM_RETRY
    async def structured_outputs_async(self, message: str, data_model):
        # NOTE:The Anthropic model does not support structured output.
        if self.llm_name in CLAUDE_MODEL.__args__:
            raise NotImplementedError(
                "Structured output is not supported for Anthropic models."
            )
        return await self.client.structured_outputs_async(
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
