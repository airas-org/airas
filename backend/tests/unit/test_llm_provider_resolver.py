import pytest

from airas.core.types.llm_provider import LLMProvider
from airas.infra.litellm_client import PROVIDER_REQUIRED_ENV_VARS
from airas.infra.llm_provider_resolver import (
    PROVIDER_PRIMARY_KEY,
    detect_available_providers,
    infer_provider,
)


@pytest.mark.parametrize(
    ("model_name", "expected"),
    [
        # Vercel AI Gateway: the upstream vendor prefix survives after the
        # gateway segment, so these must not be mistaken for the vendor's
        # own provider (openrouter/anthropic/openai/google).
        ("vercel_ai_gateway/anthropic/claude-sonnet-4", LLMProvider.VERCEL_AI_GATEWAY),
        ("vercel_ai_gateway/openai/gpt-5", LLMProvider.VERCEL_AI_GATEWAY),
        ("vercel_ai_gateway/google/gemini-2.5-pro", LLMProvider.VERCEL_AI_GATEWAY),
        ("vercel_ai_gateway/moonshotai/kimi-k2", LLMProvider.VERCEL_AI_GATEWAY),
        # Other explicit litellm-style prefixes stay unaffected.
        ("gemini/gemini-2.5-pro", LLMProvider.GOOGLE),
        ("openrouter/openai/gpt-5-nano", LLMProvider.OPENROUTER),
        ("bedrock/anthropic.claude-3-5-sonnet", LLMProvider.BEDROCK),
        # Bare model names.
        ("gpt-5", LLMProvider.OPENAI),
        ("claude-sonnet-4", LLMProvider.ANTHROPIC),
        # Unknown vendors have no provider.
        ("some-unknown-model", None),
        ("nosuchprovider/some-model", None),
    ],
)
def test_infer_provider(model_name: str, expected: LLMProvider | None) -> None:
    assert infer_provider(model_name) == expected


def test_vercel_gateway_has_a_primary_key() -> None:
    """The dashboard resolves a model's API key through this table."""
    assert (
        PROVIDER_PRIMARY_KEY[LLMProvider.VERCEL_AI_GATEWAY]
        == "VERCEL_AI_GATEWAY_API_KEY"
    )


def test_vercel_gateway_is_available_when_its_key_is_set() -> None:
    available = detect_available_providers(
        PROVIDER_REQUIRED_ENV_VARS, {"VERCEL_AI_GATEWAY_API_KEY": "vck-test"}
    )
    assert available == {LLMProvider.VERCEL_AI_GATEWAY}


def test_primary_keys_are_declared_as_required() -> None:
    """A provider's primary key must be one the availability check looks for.

    Otherwise a model could resolve to a key name that never marks its
    provider configured, and requests would go out unauthenticated.
    """
    for provider, primary_key in PROVIDER_PRIMARY_KEY.items():
        assert primary_key in PROVIDER_REQUIRED_ENV_VARS[provider]


def test_dashboard_reads_all_required_provider_env_vars() -> None:
    """Guard the dashboard's env-var list against provider table changes."""
    from airas.dashboard.api import dependencies as dashboard_deps

    expected = {name for names in PROVIDER_REQUIRED_ENV_VARS.values() for name in names}
    assert set(dashboard_deps._PROVIDER_ENV_VARS) == expected
