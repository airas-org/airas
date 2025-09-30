import json
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

# TODO: Future enhancement - handle multiple experiments independently
# Currently processing all experimental variations in a single call
# Each experimental variation could ideally be processed separately
# This would enable:
# 1. Processing each dataset/model combination independently
# 2. Parallel execution of multiple experimental configurations
# 3. Incremental experiment addition without regenerating all code
# 4. Better resource utilization and more flexible experiment generation


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
    experiment_code_validation: tuple[bool, str] | None = None,
) -> ResearchHypothesis:
    client = OpenAIClient()
    env = Environment()

    template = env.from_string(derive_specific_experiments_prompt)

    data = {
        "new_method": new_method.model_dump(),  # TODO: After modifying CreateExperimentalDesign, change the location where design data is retrieved.
        "runner_type_prompt": runner_info_dict[runner_type]["prompt"],
        "secret_names": secret_names,
        "experiment_code_validation": experiment_code_validation,
    }
    messages = template.render(data)

    output, _ = client.structured_outputs(
        model_name=llm_name,
        message=messages,
        data_model=ExperimentCode,
    )

    if output is None:
        raise ValueError("No response from LLM in derive_specific_experiments.")

    output_experiment_code = ExperimentCode(**output)
    base_code = new_method.experimental_design.base_code

    output_experiment_code = _replace_unchanged_scripts(
        output_experiment_code, base_code
    )
    output = output_experiment_code.model_dump()

    save_io_on_github(
        github_repository_info=github_repository_info,
        input=messages,
        output=json.dumps(output, ensure_ascii=False, indent=4),
        subgraph_name="create_code_subgraph",
        node_name="derive_specific_experiments",
    )
    new_method.experimental_design.experiment_code = (
        output_experiment_code  # TODO: Store code for each experiment in the future
    )
    return new_method
