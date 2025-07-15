import os

import pytest
from pydantic import BaseModel

from airas.services.api_client.llm_client.google_genai_client import VERTEXAI_MODEL, GoogelGenAIClient

ALL_VERTEXAI_MODEL_NAMES = [t for t in VERTEXAI_MODEL.__args__]


@pytest.mark.parametrize("model_name", ALL_VERTEXAI_MODEL_NAMES)
def test_real_generate_all_models(model_name):
    if "GEMINI_API_KEY" not in os.environ:
        pytest.skip("GEMINI_API_KEY is not set. Skipping real API test.")

    client = GoogelGenAIClient()
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


class DummyDataModel(BaseModel):
    name: str
    description: str


@pytest.mark.parametrize("model_name", ALL_VERTEXAI_MODEL_NAMES)
def test_real_structured_outputs_all_models(model_name):
    if "GEMINI_API_KEY" not in os.environ:
        pytest.skip("GEMINI_API_KEY is not set. Skipping real API test.")

    client = GoogelGenAIClient()
    message = (
        "私の名前は田中です．エンジニアをしています．"
        "次の形式で出力してください。"
        "name: あなたの名前, description: あなたについて短く説明してください。"
    )

    try:
        output, cost = client.structured_outputs(
            model_name=model_name,
            message=message,
            data_model=DummyDataModel,
        )
        assert isinstance(output, dict)
        assert "name" in output and "description" in output
        assert isinstance(cost, float)
    except Exception as e:
        pytest.fail(f"API call failed for model {model_name}: {e}")
