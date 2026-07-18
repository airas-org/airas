import os
from collections.abc import Callable
from typing import Annotated
from uuid import UUID

import httpx
from dependency_injector.wiring import Provide, Provider, inject
from fastapi import Depends, HTTPException, status

from airas.container import Container
from airas.core.credentials import refresh_environment
from airas.infra.github_client import GithubClient
from airas.infra.langchain_client import (
    PROVIDER_REQUIRED_ENV_VARS as LANGCHAIN_REQUIRED_ENV_VARS,
)
from airas.infra.langchain_client import LangChainClient
from airas.infra.litellm_client import (
    PROVIDER_REQUIRED_ENV_VARS as LITELLM_REQUIRED_ENV_VARS,
)
from airas.infra.litellm_client import LiteLLMClient
from airas.infra.llm_provider_resolver import (
    PROVIDER_PRIMARY_KEY,
    detect_available_providers,
    infer_provider,
)

# FastAPI dependencies that resolve credentials from environment variables
# and assemble clients. Session lifecycle is managed by the Container.
# ~/.airas/credentials.json (editable from the settings page) is re-read on
# every resolution and overrides plain environment variables.

SYSTEM_USER_ID = UUID("00000000-0000-0000-0000-000000000001")

_PROVIDER_ENV_VARS = ("OPENAI_API_KEY", "ANTHROPIC_API_KEY", "GEMINI_API_KEY")

_NO_LLM_PROVIDERS = HTTPException(
    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
    detail="No LLM provider API keys are configured. Set at least one provider's API key.",
)


def get_current_user_id() -> UUID:
    """Single-user deployment: every request acts as the system user."""
    return SYSTEM_USER_ID


def get_github_owner() -> str:
    """Return the GitHub owner configured via environment variable."""
    refresh_environment()
    if not (owner := os.getenv("GITHUB_OWNER", "")):
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="GITHUB_OWNER environment variable is not set.",
        )
    return owner


def _resolve_github_token() -> str:
    refresh_environment()
    token = os.getenv("GH_PERSONAL_ACCESS_TOKEN", "")
    if not token:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="GH_PERSONAL_ACCESS_TOKEN is not configured.",
        )
    return token


def _resolve_env_keys() -> dict[str, str]:
    """Read LLM API keys from the environment (credentials file included)."""
    refresh_environment()
    return {env: val for env in _PROVIDER_ENV_VARS if (val := os.getenv(env, ""))}


def _create_key_fn(keys: dict[str, str]) -> Callable[[str], str | None]:
    def _resolve(model_name: str) -> str | None:
        provider = infer_provider(model_name)
        if provider is None:
            return None
        env_var = PROVIDER_PRIMARY_KEY.get(provider)
        if env_var is None:
            return None
        return keys.get(env_var)

    return _resolve


@inject
def get_langchain_client(
    langchain_client_factory: Annotated[
        Callable[..., LangChainClient],
        Depends(Provider[Container.langchain_client]),
    ],
) -> LangChainClient:
    """Create a LangChainClient via Container with env-provided API keys."""
    keys = _resolve_env_keys()
    available = detect_available_providers(LANGCHAIN_REQUIRED_ENV_VARS, keys)
    if not available:
        raise _NO_LLM_PROVIDERS
    return langchain_client_factory(
        get_api_key=_create_key_fn(keys),
        available_providers=available,
    )


@inject
def get_litellm_client(
    litellm_client_factory: Annotated[
        Callable[..., LiteLLMClient],
        Depends(Provider[Container.litellm_client]),
    ],
) -> LiteLLMClient:
    """Create a LiteLLMClient via Container with env-provided API keys."""
    keys = _resolve_env_keys()
    available = detect_available_providers(LITELLM_REQUIRED_ENV_VARS, keys)
    if not available:
        raise _NO_LLM_PROVIDERS
    return litellm_client_factory(
        get_api_key=_create_key_fn(keys),
        available_providers=available,
    )


@inject
async def get_github_client(
    github_sync_session: Annotated[
        httpx.Client, Depends(Provide[Container.github_sync_session])
    ],
    github_async_session: Annotated[
        httpx.AsyncClient, Depends(Provide[Container.github_async_session])
    ],
) -> GithubClient:
    return GithubClient(
        github_token=_resolve_github_token(),
        sync_session=github_sync_session,
        async_session=github_async_session,
    )


@inject
async def get_github_client_or_none(
    github_sync_session: Annotated[
        httpx.Client, Depends(Provide[Container.github_sync_session])
    ],
    github_async_session: Annotated[
        httpx.AsyncClient, Depends(Provide[Container.github_async_session])
    ],
) -> GithubClient | None:
    """Like get_github_client, but yields None when no token is configured.

    For endpoints where GitHub access is only one of several modes (e.g. the
    Overleaf export, which can read from a local clone instead).
    """
    refresh_environment()
    if not os.getenv("GH_PERSONAL_ACCESS_TOKEN", ""):
        return None
    return GithubClient(
        github_token=_resolve_github_token(),
        sync_session=github_sync_session,
        async_session=github_async_session,
    )
