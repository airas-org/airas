"""How OpenAI-compatible endpoints (e.g. `rikyu/<model>`) reach litellm.

litellm has no provider per institutional endpoint, so the client rewrites
the model name and supplies the host itself. These tests pin that mapping,
since getting it wrong sends research traffic to the wrong host — or to a
vendor default with the wrong key.
"""

from airas.core.types.llm_provider import LLMProvider
from airas.infra.litellm_client import (
    LITELLM_OPENAI_COMPATIBLE_PREFIX,
    LiteLLMClient,
)
from airas.infra.llm_provider_resolver import OPENAI_COMPATIBLE_ENDPOINTS

RIKYU = OPENAI_COMPATIBLE_ENDPOINTS[LLMProvider.RIKYU]


def test_vendor_models_pass_through_untouched() -> None:
    client = LiteLLMClient(get_api_key=lambda _: "sk-vendor", available_providers=set())

    model, connection = client._resolve_call_target("openrouter/openai/gpt-5-nano")

    assert model == "openrouter/openai/gpt-5-nano"
    assert connection == {"api_key": "sk-vendor"}


def test_endpoint_model_is_routed_to_its_default_base_url(monkeypatch) -> None:
    monkeypatch.delenv(RIKYU.base_url_env, raising=False)
    client = LiteLLMClient(
        get_api_key=lambda _: "sk-endpoint", available_providers=set()
    )

    model, connection = client._resolve_call_target("rikyu/kimi-k3")

    # Only the model ID survives the rewrite; the provider name is airas's.
    assert model == f"{LITELLM_OPENAI_COMPATIBLE_PREFIX}kimi-k3"
    assert connection == {
        "api_key": "sk-endpoint",
        "api_base": RIKYU.default_base_url,
    }


def test_base_url_env_overrides_the_default(monkeypatch) -> None:
    monkeypatch.setenv(RIKYU.base_url_env, "https://staging.example.org/v1/")
    client = LiteLLMClient(
        get_api_key=lambda _: "sk-endpoint", available_providers=set()
    )

    _, connection = client._resolve_call_target("rikyu/kimi-k3")

    # The trailing slash is dropped so litellm does not build "//chat/...".
    assert connection["api_base"] == "https://staging.example.org/v1"


def test_key_falls_back_to_the_environment(monkeypatch) -> None:
    """Self-hosted callers construct the client without a key resolver."""
    monkeypatch.setenv(RIKYU.key_env, "sk-from-env")
    client = LiteLLMClient(available_providers=set())

    _, connection = client._resolve_call_target("rikyu/kimi-k3")

    assert connection["api_key"] == "sk-from-env"
