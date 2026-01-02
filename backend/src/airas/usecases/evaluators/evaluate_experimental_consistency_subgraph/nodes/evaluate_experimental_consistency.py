from logging import getLogger

from jinja2 import Environment
from pydantic import BaseModel

from airas.core.types.research_hypothesis import (
    ExperimentEvaluation,
    ResearchHypothesis,
)
from airas.infra.langchain_client import LangChainClient
from airas.infra.llm_specs import LLM_MODELS

logger = getLogger(__name__)


class LLMOutput(BaseModel):
    consistency_feedback: str
    consistency_score: int


def evaluate_experimental_consistency(
    llm_name: LLM_MODELS,
    prompt_template: str,
    new_method: ResearchHypothesis,
    consistency_score_threshold: int = 7,
    client: LangChainClient | None = None,
) -> ResearchHypothesis:
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

        output, _ = client.structured_outputs(
            llm_name=llm_name, message=messages, data_model=LLMOutput
        )

        if output is None:
            logger.error(
                f"No response from LLM for experiment {experiment.experiment_id}"
            )
            continue

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
