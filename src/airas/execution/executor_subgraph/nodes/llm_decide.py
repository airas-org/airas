from logging import getLogger

from jinja2 import Environment
from pydantic import BaseModel

from airas.execution.executor_subgraph.prompt.llm_decide import (
    llm_decide_prompt,
)
from airas.utils.api_client.llm_facade_client import LLM_MODEL, LLMFacadeClient

logger = getLogger(__name__)


class LLMOutput(BaseModel):
    judgment_result: bool


def llm_decide(
    llm_name: LLM_MODEL,
    output_text_data: str,
    error_text_data: str,
    prompt_template: str = llm_decide_prompt,
) -> bool | None:
    client = LLMFacadeClient(llm_name)

    data = {"output_text_data": output_text_data, "error_text_data": error_text_data}

    env = Environment()
    template = env.from_string(prompt_template)
    messages = template.render(data)
    output, cost = client.structured_outputs(
        message=messages,
        data_model=LLMOutput,
    )
    if "judgment_result" in output:
        judgment_result = output["judgment_result"]
        return judgment_result
    else:
        raise ValueError("Error: No response from LLM in llm_decide.")


if __name__ == "__main__":
    llm_name = "gpt-4o-mini-2024-07-18"
    output_text_data = "No error"
    error_text_data = "Error"
    result = llm_decide(llm_name, output_text_data, error_text_data)
    print(result)
