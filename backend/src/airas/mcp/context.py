import os
from typing import Any

import httpx
from pydantic import BaseModel

from airas.core.credentials import SETUP_INSTRUCTIONS, refresh_environment
from airas.core.types.llm_provider import LLMProvider
from airas.infra.airas_db_index import AirasDbPaperSearchIndex
from airas.infra.airas_records_client import AirasRecordsClient
from airas.infra.airas_records_index import AirasRecordsIndex
from airas.infra.arxiv_client import ArxivClient
from airas.infra.github_client import GithubClient
from airas.infra.hugging_face_client import HuggingFaceClient
from airas.infra.kroki_client import KrokiClient
from airas.infra.litellm_client import (
    PROVIDER_REQUIRED_ENV_VARS as LITELLM_PROVIDER_REQUIRED_ENV_VARS,
)
from airas.infra.litellm_client import (
    LiteLLMClient,
)
from airas.infra.llm_provider_resolver import (
    detect_available_providers,
)
from airas.infra.openalex_client import OpenAlexClient
from airas.infra.run_output_store import RunOutputStore, build_store
from airas.infra.semantic_scholar_client import SemanticScholarClient
from airas.infra.seyval_client import SeyvalClient

# BM25 index over the AIRAS papers DB; built lazily on first search and
# reused for the lifetime of the server process.
_search_index = AirasDbPaperSearchIndex()

# Process-lifetime HTTP sessions (the stdio server exits with the client,
# so these are closed by process teardown).
_GITHUB_TIMEOUT = httpx.Timeout(connect=10.0, read=60.0, write=120.0, pool=5.0)
_github_sync_session = httpx.Client(follow_redirects=True, timeout=_GITHUB_TIMEOUT)
_github_async_session = httpx.AsyncClient(
    follow_redirects=True, timeout=_GITHUB_TIMEOUT
)
_sync_session = httpx.Client(follow_redirects=True)
_async_session = httpx.AsyncClient(follow_redirects=True)

# BM25 index over the research records AIRAS produced; built on first search.
_records_index = AirasRecordsIndex(AirasRecordsClient(async_session=_async_session))


def _github_client() -> GithubClient:
    refresh_environment()
    token = os.getenv("GH_PERSONAL_ACCESS_TOKEN", "")
    if not token:
        raise RuntimeError(
            f"GH_PERSONAL_ACCESS_TOKEN is not configured. {SETUP_INSTRUCTIONS}"
        )

    return GithubClient(
        github_token=token,
        sync_session=_github_sync_session,
        async_session=_github_async_session,
    )


def _seyval_client() -> SeyvalClient:
    refresh_environment()
    if not os.getenv("SEYVAL_API_KEY"):
        raise RuntimeError(f"SEYVAL_API_KEY is not configured. {SETUP_INSTRUCTIONS}")

    return SeyvalClient(sync_session=_sync_session, async_session=_async_session)


def _output_store(backend: str, git_url: str) -> RunOutputStore:
    return build_store(
        backend, git_url, seyval_client=_seyval_client, github_client=_github_client
    )


def _kroki_client() -> KrokiClient:
    refresh_environment()
    return KrokiClient(sync_session=_sync_session, async_session=_async_session)


def _arxiv_client() -> ArxivClient:
    return ArxivClient(sync_session=_sync_session, async_session=_async_session)


def _openalex_client() -> OpenAlexClient:
    refresh_environment()  # OPENALEX_API_KEY is optional
    return OpenAlexClient(sync_session=_sync_session, async_session=_async_session)


def _hugging_face_client() -> HuggingFaceClient:
    refresh_environment()  # HF_TOKEN is optional for public resources
    return HuggingFaceClient(sync_session=_sync_session, async_session=_async_session)


def _semantic_scholar_client() -> SemanticScholarClient:
    refresh_environment()  # SEMANTIC_SCHOLAR_API_KEY is optional
    return SemanticScholarClient(
        sync_session=_sync_session, async_session=_async_session
    )


def _litellm_client() -> LiteLLMClient:
    refresh_environment()
    if not detect_available_providers(LITELLM_PROVIDER_REQUIRED_ENV_VARS):
        raise RuntimeError(
            f"No LLM provider API keys are configured. {SETUP_INSTRUCTIONS}"
        )
    return LiteLLMClient()


# airas's LLMProvider enum value -> litellm's ``custom_llm_provider`` name.
# Only GOOGLE and RIKYU diverge (airas "google" vs litellm "gemini"; "rikyu"
# is an airas name for litellm's generic OpenAI-compatible route); every
# other provider's enum value already matches litellm, so we fall back to it.
_LITELLM_PROVIDER_NAME: dict[LLMProvider, str] = {
    LLMProvider.GOOGLE: "gemini",
    LLMProvider.RIKYU: "hosted_vllm",
}


def _dump(value: Any) -> Any:
    return value.model_dump() if isinstance(value, BaseModel) else value
