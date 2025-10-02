import json
import logging
import re

from jinja2 import Environment

from airas.config.runner_type_info import RunnerType, runner_info_dict
from airas.features.create.create_code_subgraph.prompt.derive_specific_experiments_prompt import (
    derive_specific_experiments_prompt,
)
from airas.services.api_client.llm_client.openai_client import (
    OPENAI_MODEL,
    OpenAIClient,
)
from airas.types.github import GitHubRepositoryInfo
from airas.types.research_hypothesis import ExperimentCode, ResearchHypothesis
from airas.utils.save_prompt import save_io_on_github

logger = logging.getLogger(__name__)

# TODO: Refactor LLM calls to use async/await for better performance
# Current implementation: Sequential LLM calls for each experiment (synchronous)
# Future enhancement: Convert to async implementation
# Benefits:
# 1. Concurrent processing of multiple experiments
# 2. Reduced total execution time when processing multiple Experiment objects
# 3. Better resource utilization
# Implementation approach:
# - Convert derive_specific_experiments to async function
# - Use asyncio.gather() to process all experiments concurrently
# - Update OpenAIClient to support async calls (or use existing async methods)


def _replace_unchanged_scripts(
    output_code: ExperimentCode, base_code: ExperimentCode
) -> ExperimentCode:
    unchanged_patterns = [
        r"\[UNCHANGED\]",
        r"\b\w*PLACEHOLDER\w*\b",
        r"\bno\s+changes\s+needed\b",
        r"\bremains\s+the\s+same\b",
        r"\bunchanged\b",
        r"\bnot\s+modified\b",
    ]

    output_dict = output_code.model_dump()
    base_dict = base_code.model_dump()

    for field_name, field_value in output_dict.items():
        for pattern in unchanged_patterns:
            if re.search(pattern, field_value, re.IGNORECASE):
                if field_name in base_dict:
                    output_dict[field_name] = base_dict[field_name]
                break

    return ExperimentCode(**output_dict)


def derive_specific_experiments(
    llm_name: OPENAI_MODEL,
    new_method: ResearchHypothesis,
    runner_type: RunnerType,
    secret_names: list[str],
    github_repository_info: GitHubRepositoryInfo,
    experiment_code_validation: dict[str, tuple[bool, str]] | None = None,
) -> ResearchHypothesis:
    client = OpenAIClient(reasoning_effort="high")
    env = Environment()
    template = env.from_string(derive_specific_experiments_prompt)
    base_code = new_method.experimental_design.base_code

    for experiment in new_method.experimental_design.experiments:
        validation_result = (
            experiment_code_validation.get(experiment.experiment_id, (False, ""))
            if experiment_code_validation
            else (False, "")
        )
        is_ready, _ = validation_result
        if is_ready:
            logger.info(
                f"Skipping experiment {experiment.experiment_id} - already validated"
            )
            continue

        data = {
            "new_method": new_method.model_dump(),
            "current_experiment": experiment.model_dump(),
            "runner_type_prompt": runner_info_dict[runner_type]["prompt"],
            "secret_names": secret_names,
            "experiment_code_validation": validation_result,
        }
        messages = template.render(data)

        output, _ = client.structured_outputs(
            model_name=llm_name,
            message=messages,
            data_model=ExperimentCode,
        )

        if output is None:
            raise ValueError(
                f"No response from LLM for experiment {experiment.experiment_id}"
            )

        output_experiment_code = ExperimentCode(**output)
        output_experiment_code = _replace_unchanged_scripts(
            output_experiment_code, base_code
        )

        save_io_on_github(
            github_repository_info=github_repository_info,
            input=messages,
            output=json.dumps(
                output_experiment_code.model_dump(), ensure_ascii=False, indent=4
            ),
            subgraph_name="create_code_subgraph",
            node_name=f"derive_specific_experiments_{experiment.experiment_id}",
        )

        # Store code in the Experiment object
        experiment.code = output_experiment_code

    return new_method
