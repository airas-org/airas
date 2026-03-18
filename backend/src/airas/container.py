import os
from collections.abc import AsyncGenerator, Generator
from typing import TypeVar

import httpx
from dependency_injector import containers, providers
from hishel import CacheOptions, SpecificationPolicy
from hishel.httpx import AsyncCacheClient, SyncCacheClient
from sqlalchemy.orm import sessionmaker
from sqlmodel import Session, create_engine

from airas.infra.arxiv_client import ArxivClient
from airas.infra.github_client import GithubClient
from airas.infra.hugging_face_client import HuggingFaceClient
from airas.infra.langchain_client import LangChainClient
from airas.infra.langfuse_client import LangfuseClient
from airas.infra.litellm_client import LiteLLMClient
from airas.infra.openalex_client import OpenAlexClient
from airas.infra.qdrant_client import QdrantClient
from airas.infra.semantic_scholar_client import SemanticScholarClient
from airas.repository.user_api_key_repository import UserApiKeyRepository
from airas.repository.user_github_token_repository import UserGitHubTokenRepository
from airas.repository.user_plan_repository import UserPlanRepository
from airas.repository.verification_repository import VerificationRepository
from airas.usecases.autonomous_research.sql_e2e_research_service import (
    SqlE2EResearchService,
)
from airas.usecases.ee.api_key_resolver import ApiKeyResolver
from airas.usecases.ee.api_key_service import ApiKeyService
from airas.usecases.ee.github_oauth_service import GitHubOAuthService
from airas.usecases.ee.plan_service import PlanService
from airas.usecases.retrieve.search_paper_titles_subgraph.nodes.search_paper_titles_from_airas_db import (
    AirasDbPaperSearchIndex,
)
from airas.usecases.verification.verification_service import VerificationService

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
    timeout = httpx.Timeout(connect=10.0, read=60.0, write=120.0, pool=5.0)
    client = httpx.Client(follow_redirects=True, timeout=timeout)
    yield client
    client.close()


async def init_github_async_session() -> AsyncGenerator[httpx.AsyncClient, None]:
    timeout = httpx.Timeout(connect=10.0, read=60.0, write=120.0, pool=5.0)
    client = httpx.AsyncClient(follow_redirects=True, timeout=timeout)
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
    langchain_client: providers.Factory[LangChainClient] = providers.Factory(
        LangChainClient
    )

    # --- LiteLLM Client ---
    litellm_client: providers.Factory[LiteLLMClient] = providers.Factory(LiteLLMClient)

    # --- Observability ---
    langfuse_client: providers.Factory[LangfuseClient] = providers.Factory(
        LangfuseClient
    )

    # --- Code & Experiment Platforms ---
    # NOTE: github_client in the container uses GH_PERSONAL_ACCESS_TOKEN as fallback.
    # In EE mode, use get_github_client() FastAPI dependency instead (per-user OAuth token).
    github_client: providers.Factory[GithubClient] = providers.Factory(
        GithubClient,
        github_token=os.getenv("GH_PERSONAL_ACCESS_TOKEN", ""),
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

    # --- Vector Database ---
    qdrant_client: providers.Factory[QdrantClient] = providers.Factory(
        QdrantClient,
        sync_session=sync_session,
        async_session=async_session,
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
        class_=Session,
        expire_on_commit=False,
        autoflush=False,
        autocommit=False,
    )

    db_session = providers.Factory(
        lambda session_factory: session_factory(),
        session_factory=session_factory,
    )

    # --- EE: API Key & Plan Services ---
    user_api_key_repository = providers.Factory(UserApiKeyRepository, db=db_session)
    api_key_service = providers.Factory(ApiKeyService, repo=user_api_key_repository)

    user_plan_repository = providers.Factory(UserPlanRepository, db=db_session)
    plan_service = providers.Factory(PlanService, repo=user_plan_repository)

    api_key_resolver = providers.Factory(
        ApiKeyResolver,
        plan_service=plan_service,
        api_key_repo=user_api_key_repository,
    )

    # --- EE: GitHub OAuth ---
    user_github_token_repository = providers.Factory(
        UserGitHubTokenRepository, db=db_session
    )
    github_oauth_service = providers.Factory(
        GitHubOAuthService, repo=user_github_token_repository
    )

    ## --- Verification Service ---
    verification_repository = providers.Factory(VerificationRepository, db=db_session)
    verification_service = providers.Factory(
        VerificationService, repo=verification_repository
    )

    ## ---  Autonomous Research Service ---
    e2e_research_service = providers.Factory(
        SqlE2EResearchService, session_factory=session_factory
    )


container = Container()
