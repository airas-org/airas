import logging
import os
from typing import Any, get_args

from botocore.config import Config
from langchain_anthropic import ChatAnthropic
from langchain_aws import ChatBedrockConverse
from langchain_core.messages import HumanMessage
from langchain_core.messages.utils import trim_messages
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_openai import ChatOpenAI

from airas.infra.llm_specs import (
    ANTHROPIC_MODELS,
    ANTHROPIC_MODELS_FOR_OPENROUTER,
    BEDROCK_MODELS,
    GOOGLE_MODELS,
    GOOGLE_MODELS_FOR_OPENROUTER,
    LLM_MODELS,
    OPENAI_MODELS,
    OPENROUTER_MODELS,
    PROVIDER_REQUIRED_ENV_VARS,
    AnthropicParams,
    GoogleGenAIParams,
    LLMParams,
    LLMProvider,
    OpenAIParams,
    get_model_context_info,
)
from airas.infra.retry_policy import make_llm_retry_policy

logger = logging.getLogger(__name__)

_LLM_RETRY = make_llm_retry_policy()


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
        self._model_cache: dict[
            tuple[LLM_MODELS, bool, tuple[tuple[str, Any], ...] | None], object
        ] = {}
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

        provider_models: dict[LLMProvider, tuple[str, ...]] = {
            LLMProvider.OPENROUTER: get_args(OPENROUTER_MODELS),
            LLMProvider.OPENAI: get_args(OPENAI_MODELS),
            LLMProvider.ANTHROPIC: get_args(ANTHROPIC_MODELS),
            LLMProvider.GOOGLE: get_args(GOOGLE_MODELS),
            LLMProvider.BEDROCK: get_args(BEDROCK_MODELS),
        }

        for provider in provider_priority:
            if (
                provider in self._available_providers
                and llm_name in provider_models.get(provider, ())
            ):
                return provider

        raise ValueError(
            f"Model '{llm_name}' is not supported by any available provider. "
            f"Available providers: {[p.value for p in self._available_providers]}"
        )

    def _validate_params_for_model(
        self, llm_name: LLM_MODELS, params: LLMParams | None
    ) -> None:
        if params is None:
            return

        model_to_params: list[tuple[tuple[str, ...], type[LLMParams]]] = [
            (get_args(OPENAI_MODELS), OpenAIParams),
            (get_args(GOOGLE_MODELS), GoogleGenAIParams),
            (get_args(GOOGLE_MODELS_FOR_OPENROUTER), GoogleGenAIParams),
            (get_args(ANTHROPIC_MODELS), AnthropicParams),
            (get_args(ANTHROPIC_MODELS_FOR_OPENROUTER), AnthropicParams),
            (get_args(BEDROCK_MODELS), AnthropicParams),
        ]

        for models, expected_type in model_to_params:
            if llm_name in models:
                if not isinstance(params, expected_type):
                    raise ValueError(
                        f"Parameter type mismatch: model '{llm_name}' expects "
                        f"{expected_type.__name__}, got {type(params).__name__}"
                    )
                return

    def _get_langchain_kwargs(self, params: LLMParams | None) -> dict[str, Any]:
        if params is None:
            return {}

        return {
            k: v
            for k, v in params.model_dump(exclude={"provider_type"}).items()
            if v is not None
        }

    def _create_chat_model(
        self,
        llm_name: LLM_MODELS,
        web_search: bool = False,
        params: LLMParams | None = None,
    ) -> Any:
        cache_key = (
            llm_name,
            web_search,
            tuple(sorted(params.model_dump().items())) if params else None,
        )

        if cache_key in self._model_cache:
            return self._model_cache[cache_key]

        provider = self._select_provider_for_model(llm_name)
        self._validate_params_for_model(llm_name, params)
        langchain_kwargs = self._get_langchain_kwargs(params)

        logger.info(
            f"Creating chat model: llm_name={llm_name}, provider={provider.value}, "
            f"web_search={web_search}, params={params}, langchain_kwargs={langchain_kwargs}"
        )

        if provider is LLMProvider.OPENROUTER:
            base_url = os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1")
            api_key = os.getenv("OPENROUTER_API_KEY")

            model_name = f"{llm_name}:online" if web_search else llm_name

            model = ChatOpenAI(
                api_key=api_key,
                base_url=base_url,
                model=model_name,
                **langchain_kwargs,
            )

        elif provider is LLMProvider.OPENAI:
            model = ChatOpenAI(model=llm_name, **langchain_kwargs)
            if web_search:
                model = model.bind_tools([{"type": "web_search"}])

        elif provider is LLMProvider.GOOGLE:
            model = ChatGoogleGenerativeAI(model=llm_name, **langchain_kwargs)

        elif provider is LLMProvider.ANTHROPIC:
            model = ChatAnthropic(model=llm_name, **langchain_kwargs)

        elif provider is LLMProvider.BEDROCK:
            # https://reference.langchain.com/python/integrations/langchain_aws/
            region_name = os.getenv("AWS_REGION_NAME", "us-east-1")

            # Configure retry strategy with exponential backoff for throttling errors
            # Increase read_timeout to 300 seconds (5 minutes) to handle long-running LLM requests
            bedrock_config = Config(
                read_timeout=300,
                connect_timeout=60,
                retries={
                    "max_attempts": 10,
                    "mode": "adaptive",
                },
            )
            model = ChatBedrockConverse(
                model_id=llm_name,
                region_name=region_name,
                config=bedrock_config,
                **langchain_kwargs,
            )

        else:
            raise ValueError(f"Unsupported provider: {provider}")

        self._model_cache[cache_key] = model
        return model

    @_LLM_RETRY
    async def generate(
        self,
        message: str,
        llm_name: LLM_MODELS,
        params: LLMParams | None = None,
        web_search: bool = False,
    ) -> str:
        model = self._create_chat_model(llm_name, web_search, params)

        try:
            context_info = get_model_context_info(llm_name)
            max_input_tokens = context_info["max_input_tokens"]
            max_output_tokens = context_info["max_output_tokens"]

            safe_max_input_tokens = max_input_tokens - 1000
            messages = [HumanMessage(content=message)]

            trimmed_messages = trim_messages(
                messages,
                max_tokens=safe_max_input_tokens,
                token_counter=model,
                strategy="last",
                allow_partial=True,
            )

            logger.info(
                f"Token management for {llm_name}: max_input={max_input_tokens}, "
                f"max_output={max_output_tokens}, safe_input={safe_max_input_tokens}"
            )

        except Exception as e:
            logger.warning(
                f"Failed to get context info or trim messages for {llm_name}: {e}. "
                "Proceeding without trimming."
            )
            trimmed_messages = message

        response = await model.ainvoke(trimmed_messages)
        content = response.content

        # When web_search is enabled, content may be a list of content blocks
        # Extract text from the content blocks
        if isinstance(content, list):
            for item in content:
                if isinstance(item, dict) and item.get("type") == "text":
                    return item.get("text", "")
            logger.warning(
                f"No text content found in web search response for model {llm_name}"
            )
            return ""

        return content

    # NOTE: web_search with structured_outputs may return before search completes due to function_calling conflict.
    @_LLM_RETRY
    async def structured_outputs(
        self,
        llm_name: LLM_MODELS,
        message: str,
        data_model,
        params: LLMParams | None = None,
        web_search: bool = False,
    ) -> Any:
        model = self._create_chat_model(llm_name, web_search=web_search, params=params)
        try:
            context_info = get_model_context_info(llm_name)
            max_input_tokens = context_info["max_input_tokens"]
            max_output_tokens = context_info["max_output_tokens"]

            safe_max_input_tokens = max_input_tokens - 1000
            messages = [HumanMessage(content=message)]

            trimmed_messages = trim_messages(
                messages,
                max_tokens=safe_max_input_tokens,
                token_counter=model,
                strategy="last",
                allow_partial=True,
            )

            logger.info(
                f"Token management for {llm_name}: max_input={max_input_tokens}, "
                f"max_output={max_output_tokens}, safe_input={safe_max_input_tokens}"
            )

        except Exception as e:
            logger.warning(
                f"Failed to get context info or trim messages for {llm_name}: {e}. "
                "Proceeding without trimming."
            )
            trimmed_messages = message

        model_with_structure = model.with_structured_output(
            schema=data_model, method="function_calling"
        )
        response = await model_with_structure.ainvoke(trimmed_messages)
        return response
