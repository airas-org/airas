import ast
import logging
import os
import re
from typing import Literal

from google import genai
from pydantic import BaseModel

from airas.utils.logging_utils import setup_logging

setup_logging()

VERTEXAI_MODEL_INFO = {
    "gemini-2.5-pro-exp-03-25": {
        "max_input_tokens": 1048576,
        "max_output_tokens": 65536,
        "input_token_cost": 1.25 * 1 / 1000000,
        "output_token_cost": 10.0 * 1 / 1000000,
    },
    "gemini-2.5-flash-preview-04-17": {
        "max_input_tokens": 1000000,
        "max_output_tokens": 65536,
        "input_token_cost": 0.15 * 1 / 1000000,
        "output_token_cost": 0.60 * 1 / 1000000,
    },
    "gemini-2.0-flash-001": {
        "max_input_tokens": 1048576,
        "max_output_tokens": 8192,
        "input_token_cost": 0.10 * 1 / 1000000,
        "output_token_cost": 0.40 * 1 / 1000000,
    },
    "gemini-2.0-flash-lite-001": {
        "max_input_tokens": 1048576,
        "max_output_tokens": 8192,
        "input_token_cost": 0.075 * 1 / 1000000,
        "output_token_cost": 0.30 * 1 / 1000000,
    },
}

VERTEXAI_MODEL = Literal[
    "gemini-2.5-pro-exp-03-25",
    "gemini-2.5-flash-preview-04-17",
    "gemini-2.0-flash-001",
    "gemini-2.0-flash-lite-001",
]


class GoogelGenAIClient:
    def __init__(self) -> None:
        self.logger = logging.getLogger(__name__)
        self.client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

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
        input_cost = input_tokens * VERTEXAI_MODEL_INFO[model_name]["input_token_cost"]
        output_cost = (
            output_tokens * VERTEXAI_MODEL_INFO[model_name]["output_token_cost"]
        )
        return input_cost + output_cost

    def generate(
        self,
        model_name: VERTEXAI_MODEL,
        message: str,
    ) -> tuple[str | None, float]:
        if not isinstance(message, str):
            raise TypeError("message must be a string")
        message = message.encode("utf-8", "ignore").decode("utf-8")
        message = self._truncate_prompt(model_name, message)

        response = self.client.models.generate_content(
            model=model_name,
            contents=message,
        )
        output = response.text
        cost = self._calculate_cost(
            model_name,
            response.usage_metadata.prompt_token_count,
            response.usage_metadata.candidates_token_count,
        )
        return output, cost

    def structured_outputs(
        self,
        model_name: VERTEXAI_MODEL,
        message: str,
        data_model: type[BaseModel],
    ) -> tuple[dict | None, float]:
        if not isinstance(message, str):
            raise TypeError("message must be a string")
        message = message.encode("utf-8", "ignore").decode("utf-8")
        message = self._truncate_prompt(model_name, message)

        response = self.client.models.generate_content(
            model=model_name,
            contents=message,
            config={
                "response_mime_type": "application/json",
                "response_schema": list[data_model],
            },
        )
        output = response.text
        if "null" in output:
            output = re.sub(r"(?<=[:,\s])null(?=[,\s}])", "None", output)
        output = ast.literal_eval(output)[0]
        cost = self._calculate_cost(
            model_name,
            response.usage_metadata.prompt_token_count,
            response.usage_metadata.candidates_token_count,
        )
        return output, cost


if __name__ == "__main__":

    class UserModel(BaseModel):
        name: str
        age: int
        email: str

    model_name = "gemini-2.0-flash-001"
    message = """
以下の文章から，名前，年齢，メールアドレスを抽出してください。
「田中太郎さん（35歳）は、東京在住のソフトウェアエンジニアです。現在、新しいAI技術の研究に取り組んでおり、業界内でも注目を集めています。お問い合わせは、taro.tanaka@example.com までお願いします。」
"""
    genai_client = GoogelGenAIClient()
    output, cost = genai_client.generate(
        model_name=model_name,
        message=message,
    )
    print(output)
    print(cost)

    output, cost = genai_client.structured_outputs(
        model_name=model_name,
        message=message,
        data_model=UserModel,
    )
    print(output)
    print(cost)
