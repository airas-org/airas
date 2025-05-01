import os
import pytest
from pydantic import BaseModel
from airas.utils.api_client.openai_client import OpenAIClient, OPENAI_MODEL

ALL_MODEL_NAMES = [t for t in OPENAI_MODEL.__args__]


@pytest.mark.parametrize("model_name", ALL_MODEL_NAMES)
def test_real_generate_all_models(model_name):
    if "OPENAI_API_KEY" not in os.environ:
        pytest.skip("OPENAI_API_KEY is not set. Skipping real API test.")

    client = OpenAIClient()
    message = "Hello, please introduce yourself."

    try:
        output, cost = client.generate(
            model_name=model_name,
            message=message,
        )
        print(f"=== Output for model {model_name} ===")
        print(output)
        assert isinstance(output, str)
        assert len(output) > 0
        assert isinstance(cost, float)
    except Exception as e:
        pytest.fail(f"API call failed for model {model_name}: {e}")


class DummyDataModel(BaseModel):
    name: str
    description: str


@pytest.mark.parametrize("model_name", ALL_MODEL_NAMES)
def test_real_structured_outputs_all_models(model_name):
    if "OPENAI_API_KEY" not in os.environ:
        pytest.skip("OPENAI_API_KEY is not set. Skipping real API test.")

    client = OpenAIClient()
    message = (
        "My name is Tanaka. I work as an engineer. "
        "Please output in the following format: "
        "name: your name, description: a brief description about yourself."
    )

    try:
        output, cost = client.structured_outputs(
            model_name=model_name,
            message=message,
            data_model=DummyDataModel,
        )
        print(f"=== Parsed Output for model {model_name} ===")
        print(output)
        assert isinstance(output, dict)
        assert len(output) > 0
        assert isinstance(cost, float)
    except Exception as e:
        pytest.fail(f"API call failed for model {model_name}: {e}")
