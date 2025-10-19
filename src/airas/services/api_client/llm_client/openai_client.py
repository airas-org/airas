import asyncio
import json
import logging
import re
from typing import Any, Literal

import tiktoken
from openai import AsyncOpenAI, OpenAI
from pydantic import BaseModel

from airas.utils.logging_utils import setup_logging

setup_logging()

# https://platform.openai.com/docs/models
OPENAI_MODEL_INFO = {
    # Reasoning models
    "o4-mini-2025-04-16": {
        "max_input_tokens": 200000 - 100000,
        "max_output_tokens": 100000,
        "input_token_cost": 1.10 * 1 / 1000000,
        "output_token_cost": 4.40 * 1 / 1000000,
    },
    "o3-2025-04-16": {
        "max_input_tokens": 200000 - 100000,
        "max_output_tokens": 100000,
        "input_token_cost": 2.00 * 1 / 1000000,
        "output_token_cost": 8.00 * 1 / 1000000,
    },
    "o3-mini-2025-01-31": {
        "max_input_tokens": 200000 - 100000,
        "max_output_tokens": 100000,
        "input_token_cost": 1.10 * 1 / 1000000,
        "output_token_cost": 4.40 * 1 / 1000000,
    },
    "o1-pro-2025-03-19": {
        "max_input_tokens": 200000 - 100000,
        "max_output_tokens": 100000,
        "input_token_cost": 150 * 1 / 1000000,
        "output_token_cost": 600 * 1 / 1000000,
    },
    "o1-2024-12-17": {
        "max_input_tokens": 200000 - 100000,
        "max_output_tokens": 100000,
        "input_token_cost": 15 * 1 / 1000000,
        "output_token_cost": 60.00 * 1 / 1000000,
    },
    # Flagship chat models
    "gpt-5-pro-2025-10-06": {
        "max_input_tokens": 400_000 - 128_000,
        "max_output_tokens": 272_000,
        "input_token_cost": 15 * 1 / 1_000_000,
        "output_token_cost": 120 * 1 / 1_000_000,
    },
    "gpt-5-codex": {
        "max_input_tokens": 400_000 - 128_000,
        "max_output_tokens": 128_000,
        "input_token_cost": 1.25 * 1 / 1_000_000,
        "output_token_cost": 10.00 * 1 / 1_000_000,
    },
    "gpt-5-2025-08-07": {
        "max_input_tokens": 400_000 - 128_000,
        "max_output_tokens": 128_000,
        "input_token_cost": 1.25 * 1 / 1_000_000,
        "output_token_cost": 10.00 * 1 / 1_000_000,
    },
    "gpt-5-mini-2025-08-07": {
        "max_input_tokens": 400_000 - 128_000,
        "max_output_tokens": 128_000,
        "input_token_cost": 0.25 * 1 / 1_000_000,
        "output_token_cost": 2.00 * 1 / 1_000_000,
    },
    "gpt-5-nano-2025-08-07": {
        "max_input_tokens": 400_000 - 128_000,
        "max_output_tokens": 128_000,
        "input_token_cost": 0.05 * 1 / 1_000_000,
        "output_token_cost": 0.40 * 1 / 1_000_000,
    },
    "gpt-4.1-2025-04-14": {
        "max_input_tokens": 1047576 - 32768,
        "max_output_tokens": 32768,
        "input_token_cost": 2.0 * 1 / 1000000,
        "output_token_cost": 8.0 * 1 / 1000000,
    },
    "gpt-4o-2024-11-20": {
        "max_input_tokens": 128000 - 16384,
        "max_output_tokens": 16384,
        "input_token_cost": 2.50 * 1 / 1000000,
        "output_token_cost": 10.00 * 1 / 1000000,
    },
    "gpt-4o-mini-2024-07-18": {
        "max_input_tokens": 128000 - 16384,
        "max_output_tokens": 16384,
        "input_token_cost": 0.15 * 1 / 1000000,
        "output_token_cost": 0.60 * 1 / 1000000,
    },
}


OPENAI_MODEL = Literal[
    "o4-mini-2025-04-16",
    "o3-2025-04-16",
    "o3-mini-2025-01-31",
    "o1-pro-2025-03-19",
    "o1-2024-12-17",
    "gpt-5-pro-2025-10-06",
    "gpt-5-codex",
    "gpt-5-2025-08-07",
    "gpt-5-mini-2025-08-07",
    "gpt-5-nano-2025-08-07",
    "gpt-4.1-2025-04-14",
    "gpt-4o-2024-11-20",
    "gpt-4o-mini-2024-07-18",
]

ReasoningEffort = Literal["low", "medium", "high"]
# TODO?: Add error handling for models that do not support reasoning effort


class OpenAIClient:
    def __init__(self, reasoning_effort: ReasoningEffort | None = None) -> None:
        self.logger = logging.getLogger(__name__)
        self.client = OpenAI()
        self.aclient = AsyncOpenAI()
        self.reasoning_effort = reasoning_effort

    def _truncate_prompt(self, model_name: OPENAI_MODEL, message: str) -> str:
        """Shorten the prompt so that it does not exceed the maximum number of tokens."""
        max_tokens = OPENAI_MODEL_INFO[model_name].get("max_input_tokens", 4096)
        enc = tiktoken.get_encoding("cl100k_base")
        encode_tokens = enc.encode(message, disallowed_special=())

        if len(encode_tokens) > max_tokens:
            self.logger.warning(
                f"Prompt length exceeds {max_tokens} tokens. Truncating."
            )
            encode_tokens = encode_tokens[: max_tokens - 100]
        message = enc.decode(encode_tokens)
        return message

    def _calculate_cost(
        self, model_name: OPENAI_MODEL, input_tokens: int, output_tokens: int
    ) -> float:
        input_cost = input_tokens * OPENAI_MODEL_INFO[model_name]["input_token_cost"]
        output_cost = output_tokens * OPENAI_MODEL_INFO[model_name]["output_token_cost"]
        return input_cost + output_cost

    def _get_params(self) -> dict[str, Any]:
        params: dict[str, Any] = {}
        if self.reasoning_effort:
            params["reasoning"] = {"effort": self.reasoning_effort}
        return params

    def generate(
        self,
        model_name: OPENAI_MODEL,
        message: str,
    ) -> tuple[str | None, float]:
        if not isinstance(message, str):
            raise TypeError("message must be a string")
        message = message.encode("utf-8", "ignore").decode("utf-8")
        message = self._truncate_prompt(model_name, message)
        params = self._get_params()

        response = self.client.responses.create(
            model=model_name,
            input=message,
            **params,
        )
        output = response.output_text
        cost = self._calculate_cost(
            model_name,
            response.usage.input_tokens,
            response.usage.output_tokens,
        )
        return output, cost

    def structured_outputs(
        self,
        model_name: OPENAI_MODEL,
        message: str,
        data_model: type[BaseModel],
    ) -> tuple[dict | None, float]:
        return asyncio.run(
            self.structured_outputs_async(model_name, message, data_model)
        )

    async def structured_outputs_async(
        self,
        model_name: OPENAI_MODEL,
        message: str,
        data_model: type[BaseModel],
    ) -> tuple[dict | None, float]:
        if not isinstance(message, str):
            raise TypeError("message must be a string")
        message = message.encode("utf-8", "ignore").decode("utf-8")
        message = self._truncate_prompt(model_name, message)
        params = self._get_params()

        response = await self.aclient.responses.parse(
            model=model_name, input=message, text_format=data_model, **params
        )
        output = response.output_text
        output = json.loads(output)
        cost = self._calculate_cost(
            model_name,
            response.usage.input_tokens,
            response.usage.output_tokens,
        )
        return output, cost

    def text_embedding(self, message: str, model_name: str = "gemini-embedding-001"):
        return

    def web_search(
        self,
        model_name: OPENAI_MODEL,
        message: str,
    ) -> tuple[dict | None, float]:
        if not isinstance(message, str):
            raise TypeError("message must be a string")

        message = message.encode("utf-8", "ignore").decode("utf-8")
        message = self._truncate_prompt(model_name, message)

        response = self.client.responses.create(
            model=model_name,
            tools=[{"type": "web_search_preview"}],
            input=message,
        )

        assistant_msgs = [
            o
            for o in response.output
            if getattr(o, "type", None) == "message"
            and getattr(o, "role", None) == "assistant"
        ]
        if not assistant_msgs:
            self.logger.warning("No assistant response from web search")
            return None, 0.0

        assistant_content = assistant_msgs[-1].content[0].text

        match = re.search(
            r"```(?:json)?\s*\n?(.*?)\s*\n?```", assistant_content, re.DOTALL
        )
        if match:
            assistant_content = match.group(1)

        output = json.loads(assistant_content)

        cost = self._calculate_cost(
            model_name,
            response.usage.input_tokens,
            response.usage.output_tokens,
        )
        return output, cost


async def main(
    model_name: OPENAI_MODEL, message: str, data_model: type[BaseModel]
) -> None:
    client = OpenAIClient()
    output, cost = await client.structured_outputs_async(
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

    model_name = "o3-mini-2025-01-31"
    message = """
以下の文章から，名前，年齢，メールアドレスを抽出してください。
「田中太郎さん（35歳）は、東京在住のソフトウェアエンジニアです。現在、新しいAI技術の研究に取り組んでおり、業界内でも注目を集めています。お問い合わせは、taro.tanaka@example.com までお願いします。」
"""
    asyncio.run(main(model_name=model_name, message=message, data_model=UserModel))
