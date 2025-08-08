from logging import getLogger

from jinja2 import Environment
from pydantic import BaseModel

from airas.features.create.fix_code_with_devin_subgraph.prompt.llm_decide import (
    llm_decide_prompt,
)
from airas.services.api_client.llm_client.llm_facade_client import (
    LLM_MODEL,
    LLMFacadeClient,
)

logger = getLogger(__name__)


class LLMOutput(BaseModel):
    is_code_fix_needed: bool


def should_fix_code(
    llm_name: LLM_MODEL,
    output_text_data: str,
    error_text_data: str,
    prompt_template: str = llm_decide_prompt,
    client: LLMFacadeClient | None = None,
) -> bool:
    client = client or LLMFacadeClient(llm_name=llm_name)

    data = {"output_text_data": output_text_data, "error_text_data": error_text_data}

    env = Environment()
    template = env.from_string(prompt_template)
    messages = template.render(data)
    output, cost = client.structured_outputs(
        message=messages,
        data_model=LLMOutput,
    )
    if output is None:
        raise ValueError("Error: No response from LLM in should_fix_code.")
    return output["is_code_fix_needed"]


if __name__ == "__main__":
    llm_name = "gpt-4o-mini-2024-07-18"
    output_text_data = "No error"
    error_text_data = "Error"
    result = should_fix_code(llm_name, output_text_data, error_text_data)
    print(result)
