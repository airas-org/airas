import os
from collections.abc import AsyncGenerator, Generator
from typing import TypeVar

import httpx
from dependency_injector import containers, providers
from hishel import CacheOptions, SpecificationPolicy
from hishel.httpx import AsyncCacheClient, SyncCacheClient
from sqlalchemy.orm import sessionmaker
from sqlmodel import create_engine

from airas.features.retrieve.search_paper_titles_subgraph.nodes.search_paper_titles_from_airas_db import (
    AirasDbPaperSearchIndex,
)
from airas.features.session_steps.service import SessionStepService
from airas.features.sessions.service import SessionService
from airas.features.step_run_links.service import StepRunLinkService
from airas.services.api_client.arxiv_client import ArxivClient
from airas.services.api_client.github_client import GithubClient
from airas.services.api_client.hugging_face_client import HuggingFaceClient
from airas.services.api_client.langchain_client import LangChainClient
from airas.services.api_client.langfuse_client import LangfuseClient
from airas.services.api_client.openalex_client import OpenAlexClient
from airas.services.api_client.qdrant_client import QdrantClient
from airas.services.api_client.semantic_scholar_client import SemanticScholarClient

T = TypeVar("T")


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


class Container(containers.DeclarativeContainer):
    config = providers.Configuration()

    # --- HTTP Session ---
    sync_session = providers.Resource(init_sync_session)
    async_session = providers.Resource(init_async_session)

    # GitHub-specific sessions (no caching)
    github_sync_session = providers.Resource(init_github_sync_session)
    github_async_session = providers.Resource(init_github_async_session)

    # --- LangChain Client ---
    langchain_client: providers.Factory = providers.Factory(LangChainClient)

    # --- Observability ---
    langfuse_client: providers.Factory[LangfuseClient] = providers.Factory(
        LangfuseClient
    )

    # --- Code & Experiment Platforms ---
    github_client: providers.Factory[GithubClient] = providers.Factory(
        GithubClient,
        sync_session=github_sync_session,  # Use non-cached session
        async_session=github_async_session,  # Use non-cached session
    )
    hugging_face_client: providers.Factory[HuggingFaceClient] = providers.Factory(
        HuggingFaceClient,
        sync_session=sync_session,
        async_session=async_session,
    )

    # --- Academic Research APIs ---
    arxiv_client: providers.Factory[ArxivClient] = providers.Factory(
        ArxivClient,
        sync_session=sync_session,
        async_session=async_session,
    )
    semantic_scholar_client: providers.Factory[SemanticScholarClient] = (
        providers.Factory(
            SemanticScholarClient,
            sync_session=sync_session,
            async_session=None,
        )
    )
    openalex_client: providers.Factory[OpenAlexClient] = providers.Factory(
        OpenAlexClient,
        sync_session=sync_session,
        async_session=None,
    )

    # --- Database Client ---
    qdrant_client: providers.Factory = providers.Factory(
        QdrantClient,
        sync_session=sync_session,
        async_session=None,
    )

    # --- Search Index ---
    airas_db_search_index: providers.Singleton[AirasDbPaperSearchIndex] = (
        providers.Singleton(AirasDbPaperSearchIndex)
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
    session_step_service = providers.Factory(SessionStepService, db=db_session)
    step_run_link_service = providers.Factory(StepRunLinkService, db=db_session)


container = Container()
