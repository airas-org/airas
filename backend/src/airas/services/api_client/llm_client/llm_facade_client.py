from typing import Annotated, Literal, Optional

from pydantic import Field

from airas.services.api_client.llm_client.anthropic_client import (
    CLAUDE_MODEL,
    AnthropicClient,
    AnthropicParams,
)
from airas.services.api_client.llm_client.google_genai_client import (
    VERTEXAI_MODEL,
    GoogleGenAIClient,
    GoogleGenAIParams,
)
from airas.services.api_client.llm_client.openai_client import (
    OPENAI_MODEL,
    OpenAIClient,
    OpenAIParams,
)
from airas.services.api_client.llm_client.retry import LLM_RETRY

LLM_MODEL = Literal[OPENAI_MODEL, VERTEXAI_MODEL, CLAUDE_MODEL]
LLMParams = Annotated[
    OpenAIParams | GoogleGenAIParams | AnthropicParams,
    Field(discriminator="provider_type"),
]


class LLMFacadeClient:
    def __init__(
        self,
        openai_client: Optional[OpenAIClient] = None,
        anthropic_client: Optional[AnthropicClient] = None,
        google_genai_client: Optional[GoogleGenAIClient] = None,
    ):
        # For backward compatibility: A new client instance is automatically created if called without arguments.
        self.openai_client = openai_client or OpenAIClient()
        self.google_genai_client = google_genai_client or GoogleGenAIClient()
        self.anthropic_client = anthropic_client or AnthropicClient()

    def _get_client(self, llm_name: LLM_MODEL):
        if llm_name in OPENAI_MODEL.__args__:
            return self.openai_client
        elif llm_name in VERTEXAI_MODEL.__args__:
            return self.google_genai_client
        elif llm_name in CLAUDE_MODEL.__args__:
            return self.anthropic_client
        else:
            raise ValueError(f"Unsupported LLM model: {llm_name}")

    @LLM_RETRY
    async def generate(
        self, message: str, llm_name: LLM_MODEL, params: LLMParams | None = None
    ):
        client = self._get_client(llm_name)
        return await client.generate(
            model_name=llm_name, message=message, params=params
        )

    @LLM_RETRY
    async def structured_outputs(
        self,
        message: str,
        data_model,
        llm_name: LLM_MODEL,
        params: LLMParams | None = None,
    ):
        # NOTE:The Anthropic model does not support structured output.
        if llm_name in CLAUDE_MODEL.__args__:
            raise NotImplementedError(
                "Structured output is not supported for Anthropic models."
            )
        client = self._get_client(llm_name)
        return await client.structured_outputs(
            model_name=llm_name, message=message, data_model=data_model, params=params
        )

    @LLM_RETRY
    async def text_embedding(
        self, message: str, llm_name: str = "gemini-embedding-001"
    ):
        client = self._get_client(llm_name)
        return await client.text_embedding(message=message, model_name=llm_name)

    @LLM_RETRY
    async def web_search(
        self, message: str, llm_name: LLM_MODEL, params: LLMParams | None = None
    ):
        # NOTE: Perform web search using OpenAI API (only available for OpenAI models).
        client = self._get_client(llm_name)
        if not hasattr(client, "web_search"):
            raise ValueError(f"Web search not supported for {llm_name}")
        return await client.web_search(
            model_name=llm_name, message=message, params=params
        )
