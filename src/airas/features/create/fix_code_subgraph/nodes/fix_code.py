import logging
import re

from jinja2 import Environment

from airas.config.runner_type_info import RunnerType, runner_info_dict
from airas.features.create.fix_code_subgraph.prompt.code_fix_prompt import (
    code_fix_prompt,
)
from airas.services.api_client.llm_client.llm_facade_client import (
    LLM_MODEL,
    LLMFacadeClient,
)
from airas.types.research_hypothesis import ExperimentCode, ResearchHypothesis

logger = logging.getLogger(__name__)


def _is_code_meaningful(content: str | None) -> bool:
    if not content or not content.strip():
        return False

    if re.search(r".*\[KEEP_ORIGINAL_FILE\].*", content.strip()):
        return False

    lines = content.strip().split("\n")
    for line in lines:
        stripped_line = line.strip()
        if stripped_line and not stripped_line.startswith("#"):
            return True
    return False  # No meaningful code found


def fix_code(
    llm_name: LLM_MODEL,
    new_method: ResearchHypothesis,
    experiment_iteration: int,
    runner_type: RunnerType,
    secret_names: list[str],
    error_list: list[str],
    file_static_validations: dict[str, dict[str, list[str]]],
    prompt_template: str = code_fix_prompt,
    client: LLMFacadeClient | None = None,
) -> dict[str, ResearchHypothesis | list[str]]:
    client = client or LLMFacadeClient(llm_name=llm_name)

    data = {
        "experiment_iteration": experiment_iteration,
        "new_method": new_method.model_dump(),
        "runner_type_prompt": runner_info_dict[runner_type]["prompt"],
        "secret_names": secret_names,
        "error_list": error_list,  # Previous errors for analysis
        "file_static_validations": file_static_validations,  # Static validation results
    }
    env = Environment()
    template = env.from_string(prompt_template)
    messages = template.render(data)

    logger.info("Fixing code using LLM...")
    output, cost = client.structured_outputs(
        message=messages, data_model=ExperimentCode
    )
    if output is None:
        raise ValueError("Error: No response from LLM in fix_code.")

    new_method.experimental_design.experiment_code = ExperimentCode(
        train_py=output["train_py"],
        evaluate_py=output["evaluate_py"],
        preprocess_py=output["preprocess_py"],
        main_py=output["main_py"],
        pyproject_toml=output["pyproject_toml"],
        smoke_test_yaml=output["smoke_test_yaml"],
        full_experiment_yaml=output["full_experiment_yaml"],
    )

    # Only add experimental_results.error on first iteration (when no file_static_validations)
    if (
        not file_static_validations  # First iteration - no static validation yet
        and hasattr(new_method, "experimental_results")
        and new_method.experimental_results
        and new_method.experimental_results.error
    ):
        error_list.append(new_method.experimental_results.error)

    return {
        "new_method": new_method,
        "error_list": error_list[-3:],  # Keep only last 3 errors
    }
