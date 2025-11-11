from logging import getLogger

from jinja2 import Environment
from pydantic import BaseModel

from airas.features.execution.execute_experiment_subgraph.prompt.judge_execution_prompt import (
    judge_execution_prompt,
)
from airas.services.api_client.llm_client.llm_facade_client import (
    LLM_MODEL,
    LLMFacadeClient,
)

logger = getLogger(__name__)


class LLMOutput(BaseModel):
    is_experiment_successful: bool


async def judge_execution(
    llm_name: LLM_MODEL,
    llm_client: LLMFacadeClient,
    stdout_text: str,
    stderr_text: str,
    prompt_template: str = judge_execution_prompt,
) -> bool:
    data = {"stdout_text": stdout_text, "stderr_text": stderr_text}

    env = Environment()
    template = env.from_string(prompt_template)
    messages = template.render(data)
    output, cost = await llm_client.structured_outputs(
        message=messages,
        data_model=LLMOutput,
        llm_name=llm_name,
    )
    if output is None:
        raise ValueError("Error: No response from LLM in judge_execution.")
    return output["is_experiment_successful"]
