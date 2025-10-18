import json
from logging import getLogger

from jinja2 import Environment
from pydantic import BaseModel

from airas.services.api_client.llm_client.llm_facade_client import (
    LLM_MODEL,
    LLMFacadeClient,
)
from airas.types.github import GitHubRepositoryInfo
from airas.types.research_hypothesis import ExperimentEvaluation, ResearchHypothesis
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
    consistency_score_threshold: int = 7,
    client: LLMFacadeClient | None = None,
) -> ResearchHypothesis:
    client = client or LLMFacadeClient(llm_name=llm_name)
    env = Environment()
    template = env.from_string(prompt_template)

    if (
        not new_method.experimental_design
        or not new_method.experimental_design.experiments
    ):
        logger.warning("No experiments to evaluate")
        return new_method

    for experiment in new_method.experimental_design.experiments:
        if not experiment.results:
            logger.warning(
                f"Experiment {experiment.experiment_id} has no results, skipping evaluation"
            )
            continue

        messages = template.render(
            {
                "new_method": new_method.model_dump(),
                "current_experiment": experiment.model_dump(),
            }
        )

        output, _ = client.structured_outputs(message=messages, data_model=LLMOutput)

        if output is None:
            logger.error(
                f"No response from LLM for experiment {experiment.experiment_id}"
            )
            continue

        save_io_on_github(
            github_repository_info=github_repository_info,
            input=messages,
            output=json.dumps(output, ensure_ascii=False, indent=4),
            subgraph_name="evaluate_experimental_consistency_subgraph",
            node_name=f"evaluate_experimental_consistency_{experiment.experiment_id}",
        )

        consistency_score = output["consistency_score"]
        is_selected = consistency_score >= consistency_score_threshold

        experiment.evaluation = ExperimentEvaluation(
            consistency_score=consistency_score,
            consistency_feedback=output["consistency_feedback"],
            is_selected_for_paper=is_selected,
        )

        logger.info(
            f"Experiment {experiment.experiment_id}: score={consistency_score}, "
            f"selected={is_selected}"
        )

    return new_method
