from logging import getLogger

from jinja2 import Environment
from pydantic import BaseModel

from airas.services.api_client.llm_client.llm_facade_client import (
    LLM_MODEL,
    LLMFacadeClient,
)
from airas.types.github import GitHubRepositoryInfo
from airas.types.research_hypothesis import ResearchHypothesis
from airas.utils.save_prompt import save_io_on_github

logger = getLogger(__name__)


class LLMOutput(BaseModel):
    consistency_feedback: str
    consistency_score: int


def evaluate_experimental_consistency(
    llm_name: LLM_MODEL,
    prompt_template: str,
    new_method: ResearchHypothesis,
    github_repository_info: GitHubRepositoryInfo,
    existing_feedback: list[str] | None = None,
    existing_scores: list[int] | None = None,
    client: LLMFacadeClient | None = None,
) -> tuple[bool, list[str], list[int]]:
    client = client or LLMFacadeClient(llm_name=llm_name)

    env = Environment()
    template = env.from_string(prompt_template)

    messages = template.render({"new_method": new_method.model_dump()})

    output, _cost = client.structured_outputs(message=messages, data_model=LLMOutput)

    if output is None:
        raise ValueError(
            "No response from LLM in evaluate_experimental_consistency node."
        )
    save_io_on_github(
        github_repository_info=github_repository_info,
        input=messages,
        output=str(output),
        subgraph_name="evaluate_experimental_consistency_subgraph",
        node_name="evaluate_experimental_consistency",
    )
    if existing_feedback is None:
        existing_feedback = []
    if existing_scores is None:
        existing_scores = []

    consistency_score = output["consistency_score"]
    updated_scores = existing_scores + [consistency_score]

    # NOTE: If score is high enough, append empty string to avoid side effects
    if consistency_score >= 7:
        is_experiment_consistent = True
        updated_feedback = existing_feedback + [""]
    else:
        is_experiment_consistent = False
        updated_feedback = existing_feedback + [output["consistency_feedback"]]

    return (is_experiment_consistent, updated_feedback, updated_scores)
