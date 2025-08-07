from logging import getLogger

from jinja2 import Environment
from pydantic import BaseModel

from airas.features.publication.latex_subgraph.prompt.is_execution_successful import (
    is_execution_successful_prompt,
)
from airas.services.api_client.llm_client.llm_facade_client import (
    LLM_MODEL,
    LLMFacadeClient,
)

logger = getLogger(__name__)


class LLMOutput(BaseModel):
    is_successful: bool


def is_execution_successful(
    llm_name: LLM_MODEL,
    latex_text: str,
    latex_error_text: str,
    client: LLMFacadeClient | None = None,
) -> bool:
    client = client or LLMFacadeClient(llm_name=llm_name)

    data = {"latex_text": latex_text, "latex_error_text": latex_error_text}

    env = Environment()
    template = env.from_string(is_execution_successful_prompt)
    messages = template.render(data)
    output, cost = client.structured_outputs(
        message=messages,
        data_model=LLMOutput,
    )
    if output is None:
        raise ValueError("Error: No response from LLM in is_execution_successful.")
    else:
        is_successful = output["is_successful"]
        return is_successful


if __name__ == "__main__":
    llm_name = "gpt-4o-mini-2024-07-18"
    output_text_data = "No error"
    error_text_data = "Error"
    result = is_execution_successful(llm_name, output_text_data, error_text_data)
    print(result)
