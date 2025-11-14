import logging
import os
from typing import Any, Literal

from anthropic import AsyncAnthropic
from pydantic import BaseModel

from airas.utils.logging_utils import setup_logging

setup_logging()


# https://docs.anthropic.com/en/docs/about-claude/models/overview#model-comparison-table
CLAUDE_MODEL_INFO: dict[str, dict[str, Any]] = {
    "claude-opus-4-1-20250805": {
        "max_input_tokens": 200000 - 32000,
        "max_output_tokens": 32000,
        "input_token_cost": 15 / 1000000,
        "output_token_cost": 75 / 1000000,
    },
    "claude-opus-4-20250514": {
        "max_input_tokens": 200000 - 32000,
        "max_output_tokens": 32000,
        "input_token_cost": 15 / 1000000,
        "output_token_cost": 75 / 1000000,
    },
    "claude-sonnet-4-20250514": {
        "max_input_tokens": 200000 - 64000,
        "max_output_tokens": 64000,
        "input_token_cost": 3 / 1000000,
        "output_token_cost": 15 / 1000000,
    },
    "claude-3-7-sonnet-20250219": {
        "max_input_tokens": 200000 - 64000,
        "max_output_tokens": 64000,
        "input_token_cost": 3 / 1000000,
        "output_token_cost": 15 / 1000000,
    },
    "claude-3-5-haiku-20241022": {
        "max_input_tokens": 200000 - 8192,
        "max_output_tokens": 8192,
        "input_token_cost": 0.8 / 1000000,
        "output_token_cost": 4 / 1000000,
    },
}

CLAUDE_MODEL = Literal[
    "claude-opus-4-1-20250805",
    "claude-opus-4-20250514",
    "claude-sonnet-4-20250514",
    "claude-3-7-sonnet-20250219",
    "claude-3-5-haiku-20241022",
]


class AnthropicParams(BaseModel):
    provider_type: Literal["anthropic"] = "anthropic"


class AnthropicClient:
    def __init__(self) -> None:
        self.logger = logging.getLogger(__name__)
        self.aclient = AsyncAnthropic(api_key=os.environ["ANTHROPIC_API_KEY"])

    def _get_params(self, params: AnthropicParams | None) -> dict[str, Any]:
        if not params:
            return {}

        api_params: dict[str, Any] = {}
        # Future extension

        return api_params

    async def _truncate_prompt(self, model_name: CLAUDE_MODEL, message: str) -> str:
        """Shorten the prompt so that it does not exceed the maximum number of tokens."""
        count_result = await self.aclient.messages.count_tokens(
            model=model_name,
            messages=[{"role": "user", "content": f"{message}"}],
        )
        total_tokens = count_result.input_tokens
        max_tokens = int(CLAUDE_MODEL_INFO[model_name].get("max_input_tokens", 4096))

        if total_tokens > max_tokens:
            self.logger.warning(
                f"Prompt length exceeds {max_tokens} tokens. Truncating."
            )
            message = message[:max_tokens]
        return message

    def _calculate_cost(
        self, model_name: CLAUDE_MODEL, input_tokens: int, output_tokens: int
    ) -> float:
        model_info = CLAUDE_MODEL_INFO[model_name]
        if "cost_fn" in model_info:
            return model_info["cost_fn"](input_tokens, output_tokens)

        input_cost = input_tokens * model_info["input_token_cost"]
        output_cost = output_tokens * model_info["output_token_cost"]
        return input_cost + output_cost

    async def generate(
        self,
        model_name: CLAUDE_MODEL,
        message: str,
        params: AnthropicParams | None = None,
    ) -> tuple[str | None, float]:
        if not isinstance(message, str):
            raise TypeError("message must be a string")
        message = message.encode("utf-8", "ignore").decode("utf-8")
        message = await self._truncate_prompt(model_name, message)
        api_params = self._get_params(params)

        response = await self.aclient.messages.create(
            model=model_name,
            max_tokens=CLAUDE_MODEL_INFO[model_name]["max_output_tokens"],
            messages=[{"role": "user", "content": f"{message}"}],
            # NOTE: Set timeout to 900s (15 min). This prevents the SDK from raising
            # "Streaming is required..." errors for requests that may take longer than 10 minutes.
            # However, streaming mode is still the recommended approach for very long generations.
            timeout=900.0,
            **api_params,
        )
        output = response.content[0].text
        cost = self._calculate_cost(
            model_name,
            response.usage.input_tokens,
            response.usage.output_tokens,
        )
        return output, cost

    async def close(self) -> None:
        if hasattr(self, "aclient") and self.aclient:
            await self.aclient.close()


async def main() -> None:
    model_name: CLAUDE_MODEL = "claude-opus-4-20250514"
    message = """
以下の文章から，名前，年齢，メールアドレスを抽出してください。
「田中太郎さん（35歳）は、東京在住のソフトウェアエンジニアです。現在、新しいAI技術の研究に取り組んでおり、業界内でも注目を集めています。お問い合わせは、taro.tanaka@example.com までお願いします。」
"""
    anthropic_client = AnthropicClient()
    output, cost = await anthropic_client.generate(
        model_name=model_name,
        message=message,
    )
    print(output)
    print(cost)


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
