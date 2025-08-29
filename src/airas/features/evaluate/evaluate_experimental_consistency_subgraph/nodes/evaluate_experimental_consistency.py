from logging import getLogger

from jinja2 import Environment
from pydantic import BaseModel

from airas.services.api_client.llm_client.llm_facade_client import (
    LLM_MODEL,
    LLMFacadeClient,
)
from airas.types.research_hypothesis import ResearchHypothesis

logger = getLogger(__name__)


class LLMOutput(BaseModel):
    is_experiment_consistent: bool
    consistency_feedback: str


def evaluate_experimental_consistency(
    llm_name: LLM_MODEL,
    prompt_template: str,
    new_method: ResearchHypothesis,
    client: LLMFacadeClient | None = None,
) -> ResearchHypothesis:
    client = client or LLMFacadeClient(llm_name=llm_name)

    env = Environment()
    template = env.from_string(prompt_template)

    data = {"new_method": new_method.model_dump()}

    messages = template.render(data)
    llm_output, _cost = client.structured_outputs(
        message=messages, data_model=LLMOutput
    )

    if llm_output is None:
        raise ValueError(
            "No response from LLM in evaluate_experimental_consistency node."
        )

    return (llm_output["is_experiment_consistent"], llm_output["consistency_feedback"])
