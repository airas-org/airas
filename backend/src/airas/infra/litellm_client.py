"""
LiteLLM Client for unified LLM interface.

Supported providers and models:
- Providers: https://docs.litellm.ai/docs/providers
- All models: https://models.litellm.ai/

To view available models in your environment, run:
    uv run python -m airas.infra.litellm_client
"""

import json
import logging
import os
from enum import Enum
from functools import lru_cache
from typing import Any

import litellm
from litellm import get_valid_models

from airas.infra.retry_policy import make_llm_retry_policy

logger = logging.getLogger(__name__)

_LLM_RETRY = make_llm_retry_policy()


class LLMProvider(str, Enum):
    GEMINI = "gemini"
    VERTEX_AI = "vertex_ai"
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    OPENROUTER = "openrouter"
    BEDROCK = "bedrock"
    AZURE = "azure"
    VERCEL_AI_GATEWAY = "vercel_ai_gateway"


PROVIDER_REQUIRED_ENV_VARS: dict[LLMProvider, list[str]] = {
    LLMProvider.GEMINI: ["GEMINI_API_KEY"],
    LLMProvider.VERTEX_AI: ["VERTEX_PROJECT", "VERTEX_LOCATION"],
    LLMProvider.OPENAI: ["OPENAI_API_KEY"],
    LLMProvider.ANTHROPIC: ["ANTHROPIC_API_KEY"],
    LLMProvider.OPENROUTER: ["OPENROUTER_API_KEY"],
    LLMProvider.BEDROCK: ["AWS_ACCESS_KEY_ID", "AWS_SECRET_ACCESS_KEY"],
    LLMProvider.AZURE: ["AZURE_API_KEY", "AZURE_API_BASE"],
    LLMProvider.VERCEL_AI_GATEWAY: ["VERCEL_AI_GATEWAY_API_KEY"],
}

# TODO: Define LLMParams


class LiteLLMClient:
    def __init__(self) -> None:
        self._available_providers: set[LLMProvider] = self._detect_available_providers()
        litellm.drop_params = True
        if logger.isEnabledFor(logging.DEBUG):
            os.environ["LITELLM_LOG"] = "DEBUG"

    def _detect_available_providers(self) -> set[LLMProvider]:
        available: set[LLMProvider] = set()
        for provider, vars_ in PROVIDER_REQUIRED_ENV_VARS.items():
            missing = [name for name in vars_ if not os.getenv(name)]
            if missing:
                continue
            available.add(provider)
        return available

    @_LLM_RETRY
    async def generate(
        self,
        message: str,
        llm_name: str,
        params: dict[str, Any] | None = None,
        web_search: bool = False,
    ) -> str:
        litellm_kwargs = params.copy() if params else {}
        messages = [{"role": "user", "content": message}]

        if web_search:
            litellm_kwargs["tools"] = [{"type": "web_search"}]

        try:
            model_info = self.get_model_info(llm_name)
            max_output_tokens = model_info.get("max_output_tokens", 4096)
            litellm_kwargs["max_tokens"] = max_output_tokens

            logger.info(
                f"Generating with model={llm_name}, web_search={web_search}, "
                f"max_tokens={max_output_tokens}, params={litellm_kwargs}"
            )
        except Exception as e:
            logger.warning(
                f"Failed to get model info for {llm_name}: {e}. "
                "Proceeding without max_tokens limit."
            )

        try:
            response = await litellm.acompletion(
                model=llm_name,
                messages=messages,
                **litellm_kwargs,
            )  # TODO: timeoutを延長する
            content = response.choices[0].message.content

            if content is None:
                logger.warning(f"Empty response from model {llm_name}")
                return ""

            return content

        except Exception as e:
            logger.error(
                f"Error generating with litellm for model {llm_name}: {e}",
                exc_info=True,
            )
            raise

    @_LLM_RETRY
    async def structured_output(
        self,
        llm_name: str,
        message: str,
        data_model,
        params: dict[str, Any] | None = None,
        web_search: bool = False,
    ) -> Any:
        litellm_kwargs = params.copy() if params else {}
        messages = [{"role": "user", "content": message}]

        if web_search:
            litellm_kwargs["tools"] = [{"type": "web_search"}]

        try:
            model_info = self.get_model_info(llm_name)
            max_output_tokens = model_info.get("max_output_tokens", 4096)
            litellm_kwargs["max_tokens"] = max_output_tokens

            logger.info(
                f"Structured output with model={llm_name}, web_search={web_search}, "
                f"schema={data_model.__name__}, max_tokens={max_output_tokens}"
            )
        except Exception as e:
            logger.warning(
                f"Failed to get model info for {llm_name}: {e}. "
                "Proceeding without max_tokens limit."
            )

        try:
            response = await litellm.acompletion(
                model=llm_name,
                messages=messages,
                response_format=data_model,
                **litellm_kwargs,
            )  # TODO: timeoutを延長する

            content = response.choices[0].message.content

            if content is None:
                raise ValueError(f"Empty response from model {llm_name}")

            if isinstance(content, data_model):
                return content

            if isinstance(content, str):
                json_data = json.loads(content)
                return data_model(**json_data)

            return data_model(**content)

        except Exception as e:
            logger.error(
                f"Error generating structured output with litellm for model {llm_name}: {e}",
                exc_info=True,
            )
            raise

    @_LLM_RETRY
    async def embedding(
        self,
        texts: list[str],
        model: str,
    ) -> list[list[float]]:
        # Try to get model info for logging and potential future use
        try:
            model_info = self.get_model_info(model)
            logger.info(
                f"Generating embeddings with model={model} for {len(texts)} texts. model_info={model_info}"
            )
        except Exception as e:
            logger.warning(
                f"Failed to get model info for {model}: {e}. Proceeding without model metadata."
            )

        try:
            response = await litellm.aembedding(model=model, input=texts)
            # Ensure we got a non-empty response
            data = getattr(response, "data", None)
            if not data:
                raise ValueError(f"Empty embedding response from model {model}")
            embeddings: list[list[float]] = [item.embedding for item in data]
            return embeddings
        except Exception as e:
            logger.error(
                f"Error generating embeddings with litellm for model {model}: {e}",
                exc_info=True,
            )
            raise

    # https://docs.litellm.ai/docs/set_keys#get_valid_models
    @staticmethod
    def get_valid_models(
        provider: str | None = None, check_provider_endpoint: bool = False
    ) -> list[str]:
        return get_valid_models(
            check_provider_endpoint=check_provider_endpoint,
            custom_llm_provider=provider,
        )

    # https://github.com/BerriAI/litellm/blob/main/model_prices_and_context_window.json
    @staticmethod
    @lru_cache(maxsize=128)
    def get_model_info(model_name: str) -> dict[str, Any]:
        return litellm.get_model_info(model_name)

    @property
    def available_providers(self) -> set[LLMProvider]:
        return self._available_providers


if __name__ == "__main__":
    print("=" * 80)
    print("LiteLLM Supported Models")
    print("=" * 80)
    print("\nOfficial Documentation:")
    print("- Providers: https://docs.litellm.ai/docs/providers")
    print("- All models: https://models.litellm.ai/")
    print("\n" + "=" * 80)

    client = LiteLLMClient()

    print("\nAvailable Providers (based on environment variables):")
    if client.available_providers:
        for provider in sorted(client.available_providers, key=lambda p: p.value):
            print(f"  ✓ {provider.value}")
    else:
        print("  (No providers configured)")

    print("\n" + "=" * 80)
    print("\nFetching models from configured providers...")
    print("=" * 80)

    provider_names = [
        "openai",
        "anthropic",
        "gemini",
        "vertex_ai",
        "bedrock",
        "openrouter",
        "azure",
        "vercel_ai_gateway",
    ]

    for provider_name in provider_names:
        print(f"\n[{provider_name.upper()}]")
        try:
            if models := LiteLLMClient.get_valid_models(provider=provider_name):
                for model in models:
                    print(f"  - {model}")
            else:
                print("  (No models found or not configured)")
        except Exception as e:
            print(f"  Error: {e}")

    print("\n" + "=" * 80)
