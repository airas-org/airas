import json
import logging
from typing import Literal

import tiktoken
from openai import OpenAI
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
        "input_token_cost": 10.00 * 1 / 1000000,
        "output_token_cost": 40.00 * 1 / 1000000,
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
    # 400 bad request error
    # "o1-mini-2024-09-12": {
    #     "max_input_tokens": 128000 - 65536,
    #     "max_output_tokens": 65536,
    #     "input_token_cost": 1.10 * 1 / 1000000,
    #     "output_token_cost": 4.40 * 1 / 1000000,
    # },
    # Flagship chat models
    "gpt-4.1-2025-04-14": {
        "max_input_tokens": 1047576 - 32768,
        "max_output_tokens": 32768,
        "input_token_cost": 2.0 * 1 / 1000000,
        "output_token_cost": 8.0 * 1 / 1000000,
    },
    # 4o series
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
    # "o1-mini-2024-09-12",
    "gpt-4.1-2025-04-14",
    "gpt-4o-2024-11-20",
    "gpt-4o-mini-2024-07-18",
]


class OpenAIClient:
    def __init__(self) -> None:
        self.logger = logging.getLogger(__name__)
        self.client = OpenAI()

    def _truncate_prompt(self, model_name: OPENAI_MODEL, message: str) -> str:
        """Shorten the prompt so that it does not exceed the maximum number of tokens."""
        max_tokens = OPENAI_MODEL_INFO[model_name].get("max_input_tokens", 4096)
        enc = tiktoken.get_encoding("cl100k_base")
        encode_tokens = enc.encode(message)

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

    def generate(
        self,
        model_name: OPENAI_MODEL,
        message: str,
    ) -> tuple[str | None, float]:
        if not isinstance(message, str):
            raise TypeError("message must be a string")
        message = message.encode("utf-8", "ignore").decode("utf-8")
        message = self._truncate_prompt(model_name, message)

        response = self.client.responses.create(
            model=model_name,
            input=message,
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
        if not isinstance(message, str):
            raise TypeError("message must be a string")
        message = message.encode("utf-8", "ignore").decode("utf-8")
        message = self._truncate_prompt(model_name, message)

        response = self.client.responses.parse(
            model=model_name,
            input=message,
            text_format=data_model,
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


if __name__ == "__main__":

    class UserModel(BaseModel):
        name: str
        age: int
        email: str

    openai_client = OpenAIClient()
    model_name = "o3-mini-2025-01-31"
    message = """
以下の文章から，名前，年齢，メールアドレスを抽出してください。
「田中太郎さん（35歳）は、東京在住のソフトウェアエンジニアです。現在、新しいAI技術の研究に取り組んでおり、業界内でも注目を集めています。お問い合わせは、taro.tanaka@example.com までお願いします。」
"""
    output, cost = openai_client.generate(
        model_name=model_name,
        message=message,
    )
    print(output)
    print(cost)

    output, cost = openai_client.structured_outputs(
        model_name=model_name,
        message=message,
        data_model=UserModel,
    )
    print(output)
    print(cost)
