from logging import getLogger

from jinja2 import Environment
from pydantic import BaseModel

from airas.features.create.create_code_subgraph.prompt.validate_full_experiment_prompt import (
    validate_full_experiment_prompt,
)
from airas.services.api_client.llm_client.llm_facade_client import (
    LLM_MODEL,
    LLMFacadeClient,
)
from airas.types.research_hypothesis import ResearchHypothesis

logger = getLogger(__name__)


class ValidationOutput(BaseModel):
    is_full_experiment_ready: bool
    full_experiment_issue: str


def validate_full_experiment_code(
    llm_name: LLM_MODEL,
    new_method: ResearchHypothesis,
    prompt_template: str = validate_full_experiment_prompt,
    client: LLMFacadeClient | None = None,
) -> tuple[bool, str]:
    if client is None:
        client = LLMFacadeClient(llm_name=llm_name)

    env = Environment()
    template = env.from_string(prompt_template)

    messages = template.render({"new_method": new_method.model_dump()})
    output, _ = client.structured_outputs(message=messages, data_model=ValidationOutput)

    if output is None:
        logger.error(
            "No response from LLM in validate_full_experiment_code. Defaulting to False."
        )
        return False, ""

    return output["is_full_experiment_ready"], output["full_experiment_issue"]
