"""How the Rikyu endpoint (`rikyu/<model>`) reaches litellm.

litellm has no provider for Rikyu, so the client rewrites the model name
onto litellm's generic OpenAI-compatible route and supplies the host itself.
These tests pin that mapping, since getting it wrong sends research traffic
to the wrong host — or to a vendor default with the wrong key.
"""

import pytest

from airas.infra.litellm_client import (
    DEFAULT_LLM_TIMEOUT_SECONDS,
    LITELLM_OPENAI_COMPATIBLE_PREFIX,
    LLM_TIMEOUT_ENV,
    LiteLLMClient,
    resolve_llm_timeout,
)
from airas.infra.llm_provider_resolver import (
    RIKYU_BASE_URL_ENV,
    RIKYU_DEFAULT_BASE_URL,
    RIKYU_KEY_ENV,
)


def test_vendor_models_pass_through_untouched() -> None:
    client = LiteLLMClient(get_api_key=lambda _: "sk-vendor", available_providers=set())

    model, connection = client._resolve_call_target("openrouter/openai/gpt-5-nano")

    assert model == "openrouter/openai/gpt-5-nano"
    assert connection == {"api_key": "sk-vendor"}


def test_endpoint_model_is_routed_to_its_default_base_url(monkeypatch) -> None:
    monkeypatch.delenv(RIKYU_BASE_URL_ENV, raising=False)
    client = LiteLLMClient(
        get_api_key=lambda _: "sk-endpoint", available_providers=set()
    )

    model, connection = client._resolve_call_target("rikyu/kimi-k3")

    # Only the model ID survives the rewrite; the provider name is airas's.
    assert model == f"{LITELLM_OPENAI_COMPATIBLE_PREFIX}kimi-k3"
    assert connection == {
        "api_key": "sk-endpoint",
        "api_base": RIKYU_DEFAULT_BASE_URL,
    }


def test_base_url_env_overrides_the_default(monkeypatch) -> None:
    monkeypatch.setenv(RIKYU_BASE_URL_ENV, "https://staging.example.org/v1/")
    client = LiteLLMClient(
        get_api_key=lambda _: "sk-endpoint", available_providers=set()
    )

    _, connection = client._resolve_call_target("rikyu/kimi-k3")

    # The trailing slash is dropped so litellm does not build "//chat/...".
    assert connection["api_base"] == "https://staging.example.org/v1"


def test_key_falls_back_to_the_environment(monkeypatch) -> None:
    """Self-hosted callers construct the client without a key resolver."""
    monkeypatch.setenv(RIKYU_KEY_ENV, "sk-from-env")
    client = LiteLLMClient(available_providers=set())

    _, connection = client._resolve_call_target("rikyu/kimi-k3")

    assert connection["api_key"] == "sk-from-env"


class TestLLMTimeout:
    """litellm's 600s default kills a reasoning model mid-thought.

    Measured on `rikyu/kimi-k3`: one call spent ~194s emitting its reasoning
    trace before the first answer token and ~284s in total, for a prompt far
    smaller than the generation subgraphs send. Queueing on the shared
    endpoint has separately added ~2min before the first token. There is no
    partial result to keep when the call is cut, so the work is simply lost.
    """

    def test_the_default_survives_a_long_reasoning_trace(self, monkeypatch):
        monkeypatch.delenv(LLM_TIMEOUT_ENV, raising=False)

        assert resolve_llm_timeout() == DEFAULT_LLM_TIMEOUT_SECONDS
        assert DEFAULT_LLM_TIMEOUT_SECONDS > 600, "litellm's own default"

    def test_a_deployment_can_tighten_it(self, monkeypatch):
        monkeypatch.setenv(LLM_TIMEOUT_ENV, "90")

        assert resolve_llm_timeout() == 90.0

@pytest.mark.parametrize("value", ["", "   ", "soon", "0", "-1", "nan", "inf", "-inf"])
    def test_an_unusable_value_falls_back_rather_than_failing(self, value, monkeypatch):
        """A bad env var must not take down every LLM call in the process."""
        monkeypatch.setenv(LLM_TIMEOUT_ENV, value)

        assert resolve_llm_timeout() == DEFAULT_LLM_TIMEOUT_SECONDS
