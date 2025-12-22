import inspect
import os
from collections.abc import AsyncGenerator, Generator
from functools import partial
from typing import Type, TypeVar

import httpx
from dependency_injector import containers, providers
from hishel import CacheOptions, SpecificationPolicy
from hishel.httpx import AsyncCacheClient, SyncCacheClient
from sqlalchemy.orm import sessionmaker

# Workaround for OpenAI SDK lazy initialization issue
# Initialize AsyncOpenAI.responses at import time to prevent silent failures
try:
    from openai import AsyncOpenAI

    _ = AsyncOpenAI().responses
except Exception:
    pass

from sqlmodel import create_engine

from airas.features.sessions.service import SessionService
from airas.services.api_client.arxiv_client import ArxivClient
from airas.services.api_client.github_client import GithubClient
from airas.services.api_client.hugging_face_client import HuggingFaceClient
from airas.services.api_client.langchain_client import LangChainClient
from airas.services.api_client.llm_client.anthropic_client import AnthropicClient
from airas.services.api_client.llm_client.google_genai_client import GoogleGenAIClient
from airas.services.api_client.llm_client.llm_facade_client import LLMFacadeClient
from airas.services.api_client.llm_client.openai_client import OpenAIClient
from airas.services.api_client.openalex_client import OpenAlexClient
from airas.services.api_client.qdrant_client import QdrantClient
from airas.services.api_client.semantic_scholar_client import SemanticScholarClient

LLM_ENV_KEYS = {
    "OpenAIClient": "OPENAI_API_KEY",
    "AnthropicClient": "ANTHROPIC_API_KEY",
    "GoogleGenAIClient": "GEMINI_API_KEY",
}
T = TypeVar("T")


class NullLLMClient:
    """Fallback client used when an LLM API key is missing."""

    def __init__(self, reason: str) -> None:
        self.reason = reason

    async def close(self) -> None:  # pragma: no cover - trivial
        return None

    def __getattr__(self, attr):  # pragma: no cover - runtime guard
        raise RuntimeError(self.reason)


def init_sync_session() -> Generator[httpx.Client, None, None]:
    enable_cache = os.getenv("ENABLE_HTTP_CACHE", "false").lower() == "true"

    client: httpx.Client
    if enable_cache:
        policy = SpecificationPolicy(
            cache_options=CacheOptions(
                shared=False,
                supported_methods=["GET"],
                allow_stale=False,
            )
        )
        client = SyncCacheClient(
            follow_redirects=True,
            policy=policy,
        )
    else:
        client = httpx.Client(follow_redirects=True)

    yield client
    client.close()


async def init_async_session() -> AsyncGenerator[httpx.AsyncClient, None]:
    enable_cache = os.getenv("ENABLE_HTTP_CACHE", "false").lower() == "true"

    client: httpx.AsyncClient
    if enable_cache:
        policy = SpecificationPolicy(
            cache_options=CacheOptions(
                shared=False,
                supported_methods=["GET"],
                allow_stale=False,
            )
        )
        client = AsyncCacheClient(
            follow_redirects=True,
            policy=policy,
        )
    else:
        client = httpx.AsyncClient(follow_redirects=True)

    yield client
    await client.aclose()


# NOTE:  GitHub-specific sessions (no caching to avoid stale SHA conflicts)
def init_github_sync_session() -> Generator[httpx.Client, None, None]:
    client = httpx.Client(follow_redirects=True)
    yield client
    client.close()


async def init_github_async_session() -> AsyncGenerator[httpx.AsyncClient, None]:
    client = httpx.AsyncClient(follow_redirects=True)
    yield client
    await client.aclose()


# NOTE: LLM clients are handled as separate resources because they use their own SDKs.
async def init_llm_client(
    client_class: Type[T],
) -> AsyncGenerator[T, None]:
    enable_cache = os.getenv("ENABLE_HTTP_CACHE", "false").lower() == "true"

    required_env = LLM_ENV_KEYS.get(client_class.__name__)
    if required_env and not os.getenv(required_env):
        warning = (
            f"{client_class.__name__} is disabled because {required_env} is not set. "
            "Set the environment variable to enable this LLM client."
        )
        yield NullLLMClient(warning)
        return

    if enable_cache:
        policy = SpecificationPolicy(
            cache_options=CacheOptions(
                shared=False,
                supported_methods=["GET"],
                allow_stale=False,
            )
        )
        http_client = AsyncCacheClient(
            follow_redirects=True,
            policy=policy,
        )
    else:
        http_client = None

    try:
        client = (
            client_class(http_client=http_client) if http_client else client_class()  # type: ignore[call-arg]
        )
    except TypeError:
        # Fallback if SDK doesn't support custom http_client
        client = client_class()

    yield client

    closer = getattr(client, "close", None)
    if callable(closer):
        maybe_close = closer()
        if inspect.iscoroutine(maybe_close):
            await maybe_close


class Container(containers.DeclarativeContainer):
    config = providers.Configuration()

    # --- HTTP Session ---
    sync_session = providers.Resource(init_sync_session)
    async_session = providers.Resource(init_async_session)

    # GitHub-specific sessions (no caching)
    github_sync_session = providers.Resource(init_github_sync_session)
    github_async_session = providers.Resource(init_github_async_session)

    # --- LLM Clients (Resource for default instances with lifecycle management) ---
    openai_client: providers.Resource[OpenAIClient] = providers.Resource(
        partial(init_llm_client, OpenAIClient)
    )
    anthropic_client: providers.Resource[AnthropicClient] = providers.Resource(
        partial(init_llm_client, AnthropicClient)
    )
    google_genai_client: providers.Resource[GoogleGenAIClient] = providers.Resource(
        partial(init_llm_client, GoogleGenAIClient)
    )

    # --- LLM Facade ---
    llm_facade_client: providers.Singleton[LLMFacadeClient] = providers.Singleton(
        LLMFacadeClient,
        openai_client=openai_client,
        anthropic_client=anthropic_client,
        google_genai_client=google_genai_client,
    )

    langchain_client: providers.Singleton = providers.Singleton(LangChainClient)

    # --- Code & Experiment Platforms ---
    github_client: providers.Singleton[GithubClient] = providers.Singleton(
        GithubClient,
        sync_session=github_sync_session,  # Use non-cached session
        async_session=github_async_session,  # Use non-cached session
    )
    hugging_face_client: providers.Singleton[HuggingFaceClient] = providers.Singleton(
        HuggingFaceClient,
        sync_session=sync_session,
        async_session=async_session,
    )

    # --- Academic Research APIs ---
    arxiv_client: providers.Singleton[ArxivClient] = providers.Singleton(
        ArxivClient,
        sync_session=sync_session,
        async_session=async_session,
    )
    semantic_scholar_client: providers.Singleton[SemanticScholarClient] = (
        providers.Singleton(
            SemanticScholarClient,
            sync_session=sync_session,
            async_session=None,
        )
    )
    openalex_client: providers.Singleton[OpenAlexClient] = providers.Singleton(
        OpenAlexClient,
        sync_session=sync_session,
        async_session=None,
    )

    # --- Database Client ---
    qdrant_client: providers.Singleton = providers.Singleton(
        QdrantClient,
        sync_session=sync_session,
        async_session=None,
    )

    # --- Database Session ---
    engine = providers.Singleton(
        create_engine,
        config.database_url,
        pool_pre_ping=True,
        future=True,
    )

    session_factory = providers.Singleton(
        sessionmaker,
        bind=engine,
        expire_on_commit=False,
        autoflush=False,
        autocommit=False,
    )

    db_session = providers.Factory(
        lambda session_factory: session_factory(),
        session_factory=session_factory,
    )
    session_service = providers.Factory(SessionService, db=db_session)


container = Container()
