import asyncio
import os
from typing import Any, get_args

from botocore.config import Config
from langchain_anthropic import ChatAnthropic
from langchain_aws import ChatBedrockConverse
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_openai import ChatOpenAI
from pydantic import BaseModel

from airas.services.api_client.llm_client.llm_facade_client import LLMParams
from airas.services.api_client.llm_specs import (
    ANTHROPIC_MODELS,
    BEDROCK_MODELS,
    GOOGLE_MODELS,
    LLM_MODELS,
    OPENAI_MODELS,
    OPENROUTER_MODELS,
    PROVIDER_REQUIRED_ENV_VARS,
    LLMProvider,
)


class MissingEnvironmentVariablesError(RuntimeError):
    def __init__(self, provider: LLMProvider, missing_vars: list[str]) -> None:
        self.provider = provider
        self.missing_vars = missing_vars
        msg = (
            f"Missing environment variables for provider '{provider.value}': "
            f"{', '.join(missing_vars)}"
        )
        super().__init__(msg)


class LangChainClient:
    def __init__(self) -> None:
        self._model_cache: dict[str, object] = {}
        self._available_providers: set[LLMProvider] = self._detect_available_providers()

    def _detect_available_providers(self) -> set[LLMProvider]:
        available: set[LLMProvider] = set()
        for provider, vars_ in PROVIDER_REQUIRED_ENV_VARS.items():
            missing = [name for name in vars_ if not os.getenv(name)]
            if missing:
                continue
            available.add(provider)
        return available

    def _select_provider_for_model(self, llm_name: LLM_MODELS) -> LLMProvider:
        """
        Select a provider that can handle llm_name from the available providers according to priority.
        """
        if not self._available_providers:
            raise RuntimeError(
                "No LLM providers are available. Check environment variables."
            )

        provider_priority: list[LLMProvider] = [
            LLMProvider.OPENROUTER,
            LLMProvider.OPENAI,
            LLMProvider.ANTHROPIC,
            LLMProvider.GOOGLE,
            LLMProvider.BEDROCK,
        ]

        for provider in provider_priority:
            if provider not in self._available_providers:
                continue

            if provider == LLMProvider.OPENROUTER and llm_name in get_args(
                OPENROUTER_MODELS
            ):
                return provider
            if provider == LLMProvider.OPENAI and llm_name in get_args(OPENAI_MODELS):
                return provider
            if provider == LLMProvider.GOOGLE and llm_name in get_args(GOOGLE_MODELS):
                return provider
            if provider == LLMProvider.ANTHROPIC and llm_name in get_args(
                ANTHROPIC_MODELS
            ):
                return provider
            if provider == LLMProvider.BEDROCK and llm_name in get_args(BEDROCK_MODELS):
                return provider

        raise ValueError(
            f"Model '{llm_name}' is not supported by any available provider. "
            f"Available providers: {[p.value for p in self._available_providers]}"
        )

    def _create_chat_model(self, llm_name: LLM_MODELS):
        if llm_name in self._model_cache:
            return self._model_cache[llm_name]

        provider = self._select_provider_for_model(llm_name)

        if provider is LLMProvider.OPENROUTER:
            base_url = os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1")
            api_key = os.getenv("OPENROUTER_API_KEY")

            # NOTE: When using a Google model via OpenRouter, you must add the google/ prefix.
            if llm_name in get_args(GOOGLE_MODELS):
                llm_name = "google/" + llm_name

            model = ChatOpenAI(api_key=api_key, base_url=base_url, model=llm_name)

        elif provider is LLMProvider.OPENAI:
            model = ChatOpenAI(model=llm_name)

        elif provider is LLMProvider.GOOGLE:
            model = ChatGoogleGenerativeAI(model=llm_name)

        elif provider is LLMProvider.ANTHROPIC:
            model = ChatAnthropic(model=llm_name)

        elif provider is LLMProvider.BEDROCK:
            # https://reference.langchain.com/python/integrations/langchain_aws/?_gl=1*d30ods*_gcl_au*MjA5NzEyNjYxMC4xNzY1NDI5NTc3*_ga*MjE0MTg1OTk2LjE3NjU0Mjk1Nzc.*_ga_47WX3HKKY2*czE3NjU0NjA2ODEkbzMkZzEkdDE3NjU0NjE0NTQkajYwJGwwJGgw
            region_name = os.getenv("AWS_REGION_NAME", "us-east-1")

            # Configure retry strategy with exponential backoff for throttling errors
            # Increase read_timeout to 300 seconds (5 minutes) to handle long-running LLM requests
            bedrock_config = Config(
                read_timeout=300,
                connect_timeout=60,
                retries={
                    "max_attempts": 10,  # Increased from default 4
                    "mode": "adaptive",  # Use adaptive retry mode for better throttling handling
                },
            )
            model = ChatBedrockConverse(
                model_id=llm_name,
                region_name=region_name,
                config=bedrock_config,
            )

        else:
            raise ValueError(f"Unsupported provider: {provider}")

        self._model_cache[llm_name] = model
        return model

    async def generate(
        self, message: str, llm_name: LLM_MODELS, params: LLMParams | None = None
    ) -> tuple[str, float]:
        """
        Generate a response from the specified language model given an input message.

        Args:
            message (str): The input message to send to the language model.
            llm_name (LLM_MODEL): The name of the language model to use.
            params (LLMParams | None, optional): Additional parameters for the language model. Defaults to None.

        Returns:
            tuple[str, float]: A tuple containing the generated response as a string and a float representing the cost (currently always 0.0).
        """
        model = self._create_chat_model(llm_name)
        response = await model.ainvoke(message)
        return response.content, 0.0

    async def structured_outputs(
        self,
        llm_name: LLM_MODELS,
        message: str,
        data_model,
        params: LLMParams | None = None,
    ) -> tuple[Any, float]:
        """
        Generate structured data from the specified language model by enforcing the provided schema.

        Args:
            llm_name (LLM_MODEL): The name of the language model to use.
            message (str): The input message containing the information to extract.
            data_model: The pydantic model used as the target schema for structured output.
            params (LLMParams | None, optional): Additional parameters for the language model. Defaults to None.

        Returns:
            tuple[Any, float]: A tuple containing the structured data parsed into the target schema and the cost (currently always 0.0).
        """
        model = self._create_chat_model(llm_name)
        model_with_structure = model.with_structured_output(
            schema=data_model, method="json_schema"
        )
        response = await model_with_structure.ainvoke(message)
        return response, 0.0


if __name__ == "__main__":

    class UserModel(BaseModel):
        name: str
        age: int
        email: str

    async def main() -> None:
        client = LangChainClient()

        response, _ = await client.generate(
            message="Hello, how are you?",
            # llm_name="gemini-2.5-flash-lite",
            # llm_name="gpt-5-mini-2025-08-07",
            # llm_name="claude-sonnet-4-5",
            # llm_name="anthropic/claude-sonnet-4.5",
            llm_name="global.anthropic.claude-sonnet-4-5-20250929-v1:0",
            # llm_name="openai.gpt-oss-120b-1:0",
            params=None,
        )
        print(response)

        message = """
以下の文章から，名前，年齢，メールアドレスを抽出してください。
「田中太郎さん（35歳）は、東京在住のソフトウェアエンジニアです。現在、新しいAI技術の研究に取り組んでおり、業界内でも注目を集めています。お問い合わせは、taro.tanaka@example.com までお願いします。」
"""

        structured, _ = await client.structured_outputs(
            message=message,
            data_model=UserModel,
            # llm_name="gemini-2.5-flash-lite",
            # llm_name="gpt-5-mini-2025-08-07",
            # llm_name="claude-sonnet-4-5",
            # llm_name="anthropic/claude-sonnet-4.5",
            llm_name="global.anthropic.claude-sonnet-4-5-20250929-v1:0",
            params=None,
        )
        print(structured)

    asyncio.run(main())
