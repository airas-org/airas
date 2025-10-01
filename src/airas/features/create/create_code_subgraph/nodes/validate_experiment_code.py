import json
from logging import getLogger

from jinja2 import Environment
from pydantic import BaseModel

from airas.features.create.create_code_subgraph.prompt.validate_experiment_code_prompt import (
    validate_experiment_code_prompt,
)
from airas.services.api_client.llm_client.llm_facade_client import (
    LLM_MODEL,
    LLMFacadeClient,
)
from airas.types.github import GitHubRepositoryInfo
from airas.types.research_hypothesis import ResearchHypothesis
from airas.utils.save_prompt import save_io_on_github

logger = getLogger(__name__)


class ExperimentValidationOutput(BaseModel):
    is_experiment_code_ready: bool
    experiment_code_issue: str


def validate_experiment_code(
    llm_name: LLM_MODEL,
    new_method: ResearchHypothesis,
    github_repository_info: GitHubRepositoryInfo,
    prompt_template: str = validate_experiment_code_prompt,
    llm_client: LLMFacadeClient | None = None,
) -> dict[str, tuple[bool, str]]:
    client = llm_client or LLMFacadeClient(llm_name=llm_name)
    env = Environment()
    template = env.from_string(prompt_template)

    if (
        not new_method.experimental_design
        or not new_method.experimental_design.experiments
    ):
        logger.error("No experiments found in experimental design")
        return {}

    validation_results = {}
    for experiment in new_method.experimental_design.experiments:
        if not experiment.code:
            logger.warning(
                f"No code found for experiment {experiment.experiment_id}, skipping validation"
            )
            validation_results[experiment.experiment_id] = (
                False,
                "No code generated yet",
            )
            continue

        messages = template.render(
            {
                "new_method": new_method.model_dump(),
                "current_experiment": experiment.model_dump(),
            }
        )
        output, _ = client.structured_outputs(
            message=messages, data_model=ExperimentValidationOutput
        )

        if output is None:
            logger.error(
                f"No response from LLM for experiment {experiment.experiment_id}. Defaulting to False."
            )
            validation_results[experiment.experiment_id] = (
                False,
                "No response from validation LLM",
            )
            continue

        save_io_on_github(
            github_repository_info=github_repository_info,
            input=messages,
            output=json.dumps(output, ensure_ascii=False, indent=4),
            subgraph_name="create_code_subgraph",
            node_name=f"validate_experiment_code_{experiment.experiment_id}",
        )

        validation_results[experiment.experiment_id] = (
            output["is_experiment_code_ready"],
            output["experiment_code_issue"],
        )

    return validation_results
