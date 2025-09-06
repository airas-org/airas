import os

import pytest

from airas.services.api_client.llm_client.anthropic_client import (
    CLAUDE_MODEL,
    AnthropicClient,
)

ALL_CLAUDE_MODEL_NAMES = [t for t in CLAUDE_MODEL.__args__]


@pytest.mark.parametrize("model_name", ALL_CLAUDE_MODEL_NAMES)
def test_real_generate_all_models(model_name):
    if "ANTHROPIC_API_KEY" not in os.environ:
        pytest.skip("ANTHROPIC_API_KEY is not set. Skipping real API test.")

    client = AnthropicClient()
    message = "こんにちは、自己紹介をしてください。"

    try:
        output, cost = client.generate(
            model_name=model_name,
            message=message,
        )
        assert isinstance(output, str)
        assert len(output) > 0
        assert isinstance(cost, float)
    except Exception as e:
        pytest.fail(f"API call failed for model {model_name}: {e}")
