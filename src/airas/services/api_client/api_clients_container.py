from collections.abc import AsyncGenerator, Generator

import httpx
import requests
from dependency_injector import containers, providers

# Workaround for OpenAI SDK lazy initialization issue
# Initialize AsyncOpenAI.responses at import time to prevent silent failures
try:
    from openai import AsyncOpenAI

    _ = AsyncOpenAI().responses
except Exception:
    pass

from airas.services.api_client.arxiv_client import ArxivClient
from airas.services.api_client.github_client import GithubClient
from airas.services.api_client.hugging_face_client import HuggingFaceClient
from airas.services.api_client.llm_client.anthropic_client import AnthropicClient
from airas.services.api_client.llm_client.google_genai_client import GoogleGenAIClient
from airas.services.api_client.llm_client.llm_facade_client import LLMFacadeClient
from airas.services.api_client.llm_client.openai_client import OpenAIClient
from airas.services.api_client.openalex_client import OpenAlexClient
from airas.services.api_client.semantic_scholar_client import SemanticScholarClient


def init_sync_session() -> Generator[requests.Session, None, None]:
    session = requests.Session()
    yield session
    session.close()


async def init_async_session() -> AsyncGenerator[httpx.AsyncClient, None]:
    client = httpx.AsyncClient(follow_redirects=True)
    yield client
    await client.aclose()


# NOTE: LLM clients are handled as separate resources because they use their own SDKs.
def init_openai_client_sync() -> Generator[OpenAIClient, None, None]:
    client = OpenAIClient()
    yield client
    client.close()


def init_anthropic_client_sync() -> Generator[AnthropicClient, None, None]:
    client = AnthropicClient()
    yield client
    client.close()


def init_google_genai_client_sync() -> Generator[GoogleGenAIClient, None, None]:
    client = GoogleGenAIClient()
    yield client
    client.close()


async def init_openai_client_async() -> AsyncGenerator[OpenAIClient, None]:
    client = OpenAIClient()
    yield client
    client.close()
    await client.aclose()


async def init_anthropic_client_async() -> AsyncGenerator[AnthropicClient, None]:
    client = AnthropicClient()
    yield client
    client.close()
    await client.aclose()


async def init_google_genai_client_async() -> AsyncGenerator[GoogleGenAIClient, None]:
    client = GoogleGenAIClient()
    yield client
    client.close()
    await client.aclose()


class SyncContainer(containers.DeclarativeContainer):
    # --- HTTP Session ---
    session = providers.Resource(init_sync_session)

    # --- LLM Clients ---
    openai_client: providers.Resource[OpenAIClient] = providers.Resource(
        init_openai_client_sync
    )
    anthropic_client: providers.Resource[AnthropicClient] = providers.Resource(
        init_anthropic_client_sync
    )
    google_genai_client: providers.Resource[GoogleGenAIClient] = providers.Resource(
        init_google_genai_client_sync
    )

    # --- LLM Facade ---
    llm_facade_client: providers.Factory[LLMFacadeClient] = providers.Factory(
        LLMFacadeClient,
        openai_client=openai_client,
        anthropic_client=anthropic_client,
        google_genai_client=google_genai_client,
    )
    llm_facade_provider: providers.Delegate = providers.Delegate(llm_facade_client)

    # --- Code & Experiment Platforms ---
    github_client: providers.Singleton[GithubClient] = providers.Singleton(
        GithubClient,
        sync_session=session,
        async_session=None,
    )
    hugging_face_client: providers.Singleton[HuggingFaceClient] = providers.Singleton(
        HuggingFaceClient,
        sync_session=session,
        async_session=None,
    )

    # --- Academic Research APIs ---
    arxiv_client: providers.Singleton[ArxivClient] = providers.Singleton(
        ArxivClient,
        sync_session=session,
        async_session=None,
    )
    semantic_scholar_client: providers.Singleton[SemanticScholarClient] = (
        providers.Singleton(
            SemanticScholarClient,
            sync_session=session,
            async_session=None,
        )
    )
    openalex_client: providers.Singleton[OpenAlexClient] = providers.Singleton(
        OpenAlexClient,
        sync_session=session,
        async_session=None,
    )


class AsyncContainer(containers.DeclarativeContainer):
    # --- HTTP Session ---
    session = providers.Resource(init_async_session)

    # --- LLM Clients ---
    openai_client: providers.Resource[OpenAIClient] = providers.Resource(
        init_openai_client_async
    )
    anthropic_client: providers.Resource[AnthropicClient] = providers.Resource(
        init_anthropic_client_async
    )
    google_genai_client: providers.Resource[GoogleGenAIClient] = providers.Resource(
        init_google_genai_client_async
    )

    # --- LLM Facade ---
    llm_facade_client: providers.Factory[LLMFacadeClient] = providers.Factory(
        LLMFacadeClient,
        openai_client=openai_client,
        anthropic_client=anthropic_client,
        google_genai_client=google_genai_client,
    )
    llm_facade_provider: providers.Delegate = providers.Delegate(llm_facade_client)

    # --- Code & Experiment Platforms ---
    github_client: providers.Singleton[GithubClient] = providers.Singleton(
        GithubClient,
        sync_session=None,
        async_session=session,
    )
    hugging_face_client: providers.Singleton[HuggingFaceClient] = providers.Singleton(
        HuggingFaceClient,
        sync_session=None,
        async_session=session,
    )

    # --- Academic Research APIs ---
    arxiv_client: providers.Singleton[ArxivClient] = providers.Singleton(
        ArxivClient,
        sync_session=None,
        async_session=session,
    )
    semantic_scholar_client: providers.Singleton[SemanticScholarClient] = (
        providers.Singleton(
            SemanticScholarClient,
            sync_session=None,
            async_session=session,
        )
    )
    openalex_client: providers.Singleton[OpenAlexClient] = providers.Singleton(
        OpenAlexClient,
        sync_session=None,
        async_session=session,
    )


# Create container instances for direct use
sync_container = SyncContainer()
async_container = AsyncContainer()
