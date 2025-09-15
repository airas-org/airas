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
    consistency_feedback: str
    consistency_score: int


def evaluate_experimental_consistency(
    llm_name: LLM_MODEL,
    prompt_template: str,
    new_method: ResearchHypothesis,
    existing_feedback: list[str] | None = None,
    existing_scores: list[int] | None = None,
    client: LLMFacadeClient | None = None,
) -> tuple[bool, list[str], list[int]]:
    client = client or LLMFacadeClient(llm_name=llm_name)

    env = Environment()
    template = env.from_string(prompt_template)

    messages = template.render({"new_method": new_method.model_dump()})

    llm_output, _cost = client.structured_outputs(
        message=messages, data_model=LLMOutput
    )

    if llm_output is None:
        raise ValueError(
            "No response from LLM in evaluate_experimental_consistency node."
        )

    if existing_feedback is None:
        existing_feedback = []
    if existing_scores is None:
        existing_scores = []

    consistency_score = llm_output["consistency_score"]
    updated_scores = existing_scores + [consistency_score]

    # NOTE: If score is high enough, append empty string to avoid side effects
    if consistency_score >= 7:
        is_experiment_consistent = True
        updated_feedback = existing_feedback + [""]
    else:
        is_experiment_consistent = False
        updated_feedback = existing_feedback + [llm_output["consistency_feedback"]]

    return (is_experiment_consistent, updated_feedback, updated_scores)
