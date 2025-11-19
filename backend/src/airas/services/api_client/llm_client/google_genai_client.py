import ast
import asyncio
import json
import logging
import os
import re
from typing import Any, Literal

from google import genai
from google.genai import types
from pydantic import BaseModel, Field

from airas.utils.logging_utils import setup_logging

setup_logging()


# https://ai.google.dev/gemini-api/docs/models?hl=ja
VERTEXAI_MODEL_INFO: dict[str, dict[str, Any]] = {
    "gemini-3-pro-preview": {
        "max_input_tokens": 1048576,
        "max_output_tokens": 65536,
        "cost_fn": lambda input_tokens, output_tokens: (
            (2.00 / 1000000 if input_tokens <= 200000 else 4.00 / 1000000)
            * input_tokens
            + (12.00 / 1000000 if input_tokens <= 200000 else 18.00 / 1000000)
            * output_tokens
        ),
    },
    "gemini-2.5-pro": {
        "max_input_tokens": 1048576,
        "max_output_tokens": 65536,
        "cost_fn": lambda input_tokens, output_tokens: (
            (1.25 / 1000000 if input_tokens <= 200000 else 2.50 / 1000000)
            * input_tokens
            + (10.00 / 1000000 if input_tokens <= 200000 else 15.00 / 1000000)
            * output_tokens
        ),
    },
    "gemini-2.5-flash": {
        "max_input_tokens": 1048576,
        "max_output_tokens": 65536,
        "input_token_cost": 0.30 * 1 / 1000000,
        "output_token_cost": 2.50 * 1 / 1000000,
    },
    "gemini-2.5-flash-preview-09-2025": {
        "max_input_tokens": 1048576,
        "max_output_tokens": 65536,
        "input_token_cost": 0.30 * 1 / 1000000,
        "output_token_cost": 2.50 * 1 / 1000000,
    },
    "gemini-2.5-flash-lite": {
        "max_input_tokens": 1048576,
        "max_output_tokens": 65536,
        "input_token_cost": 0.10 * 1 / 1000000,
        "output_token_cost": 0.40 * 1 / 1000000,
    },
    "gemini-2.5-flash-lite-preview-09-2025": {
        "max_input_tokens": 1048576,
        "max_output_tokens": 65536,
        "input_token_cost": 0.10 * 1 / 1000000,
        "output_token_cost": 0.40 * 1 / 1000000,
    },
    "gemini-2.0-flash": {
        "max_input_tokens": 1048576,
        "max_output_tokens": 8192,
        "input_token_cost": 0.10 * 1 / 1000000,
        "output_token_cost": 0.40 * 1 / 1000000,
    },
    "gemini-2.0-flash-lite": {
        "max_input_tokens": 1048576,
        "max_output_tokens": 8192,
        "input_token_cost": 0.075 * 1 / 1000000,
        "output_token_cost": 0.30 * 1 / 1000000,
    },
}

VERTEXAI_MODEL = Literal[
    "gemini-3-pro-preview",
    "gemini-2.5-pro",
    "gemini-2.5-flash",
    "gemini-2.5-flash-preview-09-2025",
    "gemini-2.5-flash-lite",
    "gemini-2.5-flash-lite-preview-09-2025",
    "gemini-2.0-flash",
    "gemini-2.0-flash-lite",
    "gemini-embedding-001",
]


# TODO: Add error handling for models that support thinking_config and validate thinking_budget ranges
# Currently supports gemini-2.5-pro with thinking_budget: 0 (off), 1024-32768 (fixed), -1 (dynamic)
class GoogleGenAIParams(BaseModel):
    provider_type: Literal["google_genai"] = "google_genai"
    thinking_budget: int | None = Field(
        None,
        description="Thinking budget for reasoning (0=off, 1024-32768=fixed, -1=dynamic)",
    )
    # Future extensions:
    # temperature: float | None = None
    # top_k: int | None = None
    # top_p: float | None = None


class GoogleGenAIClient:
    def __init__(self, http_client=None) -> None:
        self.logger = logging.getLogger(__name__)
        # Note: Google GenAI SDK may not support custom HTTP clients
        # If http_client is provided but not supported, it will be ignored
        if http_client:
            try:
                self.client = genai.Client(
                    api_key=os.getenv("GEMINI_API_KEY"), http_client=http_client
                )
            except TypeError:
                # Fallback if http_client parameter is not supported
                self.logger.warning(
                    "Google GenAI SDK does not support custom http_client, using default"
                )
                self.client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
        else:
            self.client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

    def _get_params(self, params: GoogleGenAIParams | None) -> dict[str, Any]:
        if not params:
            return {}

        api_params: dict[str, Any] = {}

        if params.thinking_budget is not None:
            api_params["config"] = types.GenerateContentConfig(
                thinking_config=types.ThinkingConfig(
                    thinking_budget=params.thinking_budget
                )
            )

        return api_params

    def _truncate_prompt(self, model_name: VERTEXAI_MODEL, message: str) -> str:
        """Shorten the prompt so that it does not exceed the maximum number of tokens."""
        total_tokens = self.client.models.count_tokens(
            model=model_name, contents=message
        ).total_tokens
        max_tokens = int(VERTEXAI_MODEL_INFO[model_name].get("max_input_tokens", 4096))

        if total_tokens > max_tokens:
            self.logger.warning(
                f"Prompt length exceeds {max_tokens} tokens. Truncating."
            )
            message = message[:max_tokens]
        return message

    def _calculate_cost(
        self, model_name: VERTEXAI_MODEL, input_tokens: int, output_tokens: int
    ) -> float:
        model_info = VERTEXAI_MODEL_INFO[model_name]
        if "cost_fn" in model_info:
            return model_info["cost_fn"](input_tokens, output_tokens)

        input_cost = input_tokens * model_info["input_token_cost"]
        output_cost = output_tokens * model_info["output_token_cost"]
        return input_cost + output_cost

    async def generate(
        self,
        model_name: VERTEXAI_MODEL,
        message: str,
        params: GoogleGenAIParams | None = None,
    ) -> tuple[str | None, float]:
        if not isinstance(message, str):
            raise TypeError("message must be a string")
        message = message.encode("utf-8", "ignore").decode("utf-8")
        message = self._truncate_prompt(model_name, message)
        api_params = self._get_params(params)

        response = await self.client.aio.models.generate_content(
            model=model_name,
            contents=message,
            **api_params,
        )
        output = response.text
        cost = self._calculate_cost(
            model_name,
            response.usage_metadata.prompt_token_count,
            response.usage_metadata.candidates_token_count,
        )
        return output, cost

    async def structured_outputs(
        self,
        model_name: VERTEXAI_MODEL,
        message: str,
        data_model: type[BaseModel],
        params: GoogleGenAIParams | None = None,
    ) -> tuple[dict | None, float]:
        if not isinstance(message, str):
            raise TypeError("message must be a string")
        message = message.encode("utf-8", "ignore").decode("utf-8")
        message = self._truncate_prompt(model_name, message)
        api_params = self._get_params(params)

        config = {
            "response_mime_type": "application/json",
            "response_schema": list[data_model],
        }

        # Add thinking config if present
        if "config" in api_params:
            config.update(api_params["config"].model_dump(exclude_none=True))

        response = await self.client.aio.models.generate_content(
            model=model_name,
            contents=message,
            config=config,
        )
        output = response.text
        if "null" in output:
            output = re.sub(r"(?<=[:,\s])null(?=[,\s}])", "None", output)
        try:
            output = json.loads(output)[0]
        except json.JSONDecodeError:
            output = ast.literal_eval(output)[0]

        cost = self._calculate_cost(
            model_name,
            response.usage_metadata.prompt_token_count,
            response.usage_metadata.candidates_token_count,
        )
        return output, cost

    async def text_embedding(
        self, message: str, model_name: str = "gemini-embedding-001"
    ) -> list[float]:
        result = await self.client.aio.models.embed_content(
            model=model_name, contents=message
        )
        return result.embeddings[0].values

    async def close(self) -> None:
        """Close method for consistency (Google GenAI SDK doesn't have explicit close)."""


async def main(
    model_name: VERTEXAI_MODEL, message: str, data_model: type[BaseModel]
) -> None:
    client = GoogleGenAIClient()
    output, cost = await client.structured_outputs(
        model_name=model_name,
        message=message,
        data_model=data_model,
    )
    print(output)


if __name__ == "__main__":

    class UserModel(BaseModel):
        name: str
        age: int
        email: str

    model_name = "gemini-2.5-flash"
    message = """
以下の文章から，名前，年齢，メールアドレスを抽出してください。
「田中太郎さん（35歳）は、東京在住のソフトウェアエンジニアです。現在、新しいAI技術の研究に取り組んでおり、業界内でも注目を集めています。お問い合わせは、taro.tanaka@example.com までお願いします。」
"""

    asyncio.run(main(model_name=model_name, message=message, data_model=UserModel))
