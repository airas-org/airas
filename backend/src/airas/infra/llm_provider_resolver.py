# TODO: Expose a guard/eligibility check (e.g. check_model_available(provider, available_providers))
#       so that the backend can reject unsupported model requests early and the frontend
#       can filter the model selector based on the user's available providers.

from __future__ import annotations

import os
from dataclasses import dataclass

from airas.core.types.llm_provider import LLMProvider


# ---------------------------------------------------------------------------
# OpenAI-compatible endpoints
# ---------------------------------------------------------------------------
@dataclass(frozen=True)
class OpenAICompatibleEndpoint:
    """An OpenAI-compatible API that airas addresses under its own name.

    Each endpoint gets a named provider rather than sharing one generic pair
    of env vars: a generic pair is effectively a singleton and collides as
    soon as a second such endpoint exists, and a credential named
    ``RIKYU_API_KEY`` says which host it reaches and which project is billed
    — which a generic name cannot. The implementation stays generic: adding
    the next endpoint is one entry here plus its prefix below.
    """

    key_env: str
    base_url_env: str
    # Used when *base_url_env* is unset, so only the key has to be configured.
    default_base_url: str


OPENAI_COMPATIBLE_ENDPOINTS: dict[LLMProvider, OpenAICompatibleEndpoint] = {
    LLMProvider.RIKYU: OpenAICompatibleEndpoint(
        key_env="RIKYU_API_KEY",
        base_url_env="RIKYU_API_BASE",
        default_base_url="https://api.rikyu.r-ccs.riken.jp/v1",
    ),
}


# ---------------------------------------------------------------------------
# Provider -> primary API-key env-var name
# ---------------------------------------------------------------------------
PROVIDER_PRIMARY_KEY: dict[LLMProvider, str] = {
    LLMProvider.GOOGLE: "GEMINI_API_KEY",
    LLMProvider.OPENAI: "OPENAI_API_KEY",
    LLMProvider.ANTHROPIC: "ANTHROPIC_API_KEY",
    LLMProvider.OPENROUTER: "OPENROUTER_API_KEY",
    LLMProvider.AZURE: "AZURE_API_KEY",
    LLMProvider.VERCEL_AI_GATEWAY: "VERCEL_AI_GATEWAY_API_KEY",
    LLMProvider.RIKYU: "RIKYU_API_KEY",
}


# ---------------------------------------------------------------------------
# Model-name prefix -> provider (order matters: first match wins)
# ---------------------------------------------------------------------------
_MODEL_PREFIX_TO_PROVIDER: list[tuple[str, LLMProvider]] = [
    # Explicit litellm-style prefixes
    ("gemini/", LLMProvider.GOOGLE),
    ("vertex_ai/", LLMProvider.VERTEX_AI),
    ("bedrock/", LLMProvider.BEDROCK),
    ("azure/", LLMProvider.AZURE),
    ("openrouter/", LLMProvider.OPENROUTER),
    # Gateway models keep their upstream vendor prefix after the gateway
    # segment (e.g. "vercel_ai_gateway/anthropic/claude-sonnet-4"), so this
    # entry must be matched before the vendor-prefix rules further down.
    ("vercel_ai_gateway/", LLMProvider.VERCEL_AI_GATEWAY),
    # OpenAI-compatible endpoints (see OPENAI_COMPATIBLE_ENDPOINTS). What
    # follows the prefix is the model ID the endpoint itself reports via
    # GET /v1/models, so it can be a bare name ("rikyu/kimi-k3") or carry a
    # vendor path; either way this must win over the vendor rules below.
    ("rikyu/", LLMProvider.RIKYU),
    # Bare model names (no prefix)
    ("gemini-", LLMProvider.GOOGLE),
    ("gemini-embedding-", LLMProvider.GOOGLE),
    ("gpt-", LLMProvider.OPENAI),
    ("o1-", LLMProvider.OPENAI),
    ("o3-", LLMProvider.OPENAI),
    ("o4-", LLMProvider.OPENAI),
    ("text-embedding-", LLMProvider.OPENAI),
    ("claude-", LLMProvider.ANTHROPIC),
    # Bedrock cross-region inference profile IDs
    ("jp.", LLMProvider.BEDROCK),
    ("us.", LLMProvider.BEDROCK),
    ("eu.", LLMProvider.BEDROCK),
    ("global.", LLMProvider.BEDROCK),
    # OpenRouter vendor-prefixed models
    ("google/", LLMProvider.OPENROUTER),
    ("anthropic/", LLMProvider.OPENROUTER),
    ("openai/", LLMProvider.OPENROUTER),
]


def infer_provider(model_name: str) -> LLMProvider | None:
    """Infer the LLM provider from a model name.

    Resolution strategy:
    1. Prefix-table lookup (covers most cases).
    2. Slash-prefix fallback — treats the segment before the first ``/``
       as a potential provider value (e.g. ``"openai/gpt-4"``).

    Returns ``None`` when the provider cannot be determined.
    """
    for prefix, provider in _MODEL_PREFIX_TO_PROVIDER:
        if model_name.startswith(prefix):
            return provider

    # Fallback: "provider/model" convention
    if "/" in model_name:
        candidate = model_name.split("/", 1)[0].lower()
        try:
            return LLMProvider(candidate)
        except ValueError:
            pass

    return None


def detect_available_providers(
    required_env_vars: dict[LLMProvider, list[str]],
    api_keys: dict[str, str] | None = None,
) -> set[LLMProvider]:
    """Return providers whose required credentials are present.

    When *api_keys* is given the dict is checked first; otherwise
    ``os.environ`` is consulted (backward-compatible self-host path).
    """
    available: set[LLMProvider] = set()
    for provider, vars_ in required_env_vars.items():
        if api_keys is not None:
            missing = [name for name in vars_ if name not in api_keys]
        else:
            missing = [name for name in vars_ if not os.getenv(name)]
        if not missing:
            available.add(provider)
    return available
