from logging import getLogger

from jinja2 import Environment
from pydantic import BaseModel

from airas.features.execution.github_actions_executor_subgraph.prompt.extract_required_info_prompt import (
    extract_required_info_prompt,
)
from airas.services.api_client.llm_client.llm_facade_client import (
    LLM_MODEL,
    LLMFacadeClient,
)

logger = getLogger(__name__)


class LLMOutput(BaseModel):
    extracted_output: str
    extracted_error: str


def extract_required_info(
    llm_name: LLM_MODEL,
    output_text_data: str,
    error_text_data: str,
    client: LLMFacadeClient | None = None,
) -> tuple[str, str]:
    client = client or LLMFacadeClient(llm_name=llm_name)
    env = Environment()
    template = env.from_string(extract_required_info_prompt)
    data = {
        "output_text_data": output_text_data,
        "error_text_data": error_text_data,
    }
    messages = template.render(data)
    output, cost = client.structured_outputs(
        message=messages,
        data_model=LLMOutput,
    )
    if output is None:
        raise ValueError("No response from LLM in idea_generator.")

    return output["extracted_output"], output["extracted_error"]
