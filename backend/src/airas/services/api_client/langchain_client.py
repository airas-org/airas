import asyncio
from typing import Any, get_args

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_openai import ChatOpenAI
from pydantic import BaseModel

from airas.services.api_client.llm_client.google_genai_client import VERTEXAI_MODEL
from airas.services.api_client.llm_client.llm_facade_client import LLM_MODEL, LLMParams
from airas.services.api_client.llm_client.openai_client import OPENAI_MODEL

GOOGLE_MODEL_NAMES = get_args(VERTEXAI_MODEL)
OPENAI_MODEL_NAMES = get_args(OPENAI_MODEL)


class LangChainClient:

    def _create_chat_model(self, llm_name: LLM_MODEL):
        """Return the LangChain chat model implementation that matches the LLM name."""
        if llm_name in GOOGLE_MODEL_NAMES:
            return ChatGoogleGenerativeAI(model=llm_name)
        elif llm_name in OPENAI_MODEL_NAMES:
            return ChatOpenAI(model=llm_name)
        raise ValueError(f"Unsupported LLM model: {llm_name}")

    async def generate(
        self, message: str, llm_name: LLM_MODEL, params: LLMParams | None = None
    ) -> tuple[str, float]:
        model = self._create_chat_model(llm_name)
        response = await model.ainvoke(message)
        return response.content, 0.0

    async def structured_outputs(
        self,
        llm_name: LLM_MODEL,
        message: str,
        data_model,
        params: LLMParams | None = None,
    ) -> tuple[Any, float]:
        model = self._create_chat_model(llm_name)
        model_with_structure = model.with_structured_output(
            schema=data_model, method="json_schema"
        )
        response = await model_with_structure.ainvoke(message)
        return response, 0.0


if __name__ == "__main__":

    class UserModel(BaseModel):
        name: str
        age: int
        email: str

    async def main() -> None:
        client = LangChainClient()

        response, _ = await client.generate(
            message="Hello, how are you?",
            # llm_name="gemini-2.5-flash",
            llm_name="gpt-5-mini-2025-08-07",
            params=None,
        )
        print(response)

        message = """
以下の文章から，名前，年齢，メールアドレスを抽出してください。
「田中太郎さん（35歳）は、東京在住のソフトウェアエンジニアです。現在、新しいAI技術の研究に取り組んでおり、業界内でも注目を集めています。お問い合わせは、taro.tanaka@example.com までお願いします。」
"""

        structured, _ = await client.structured_outputs(
            message=message,
            data_model=UserModel,
            # llm_name="gemini-2.5-flash",
            llm_name="gpt-5-mini-2025-08-07",
            params=None,
        )
        print(structured)

    asyncio.run(main())
