import logging
import re

from jinja2 import Environment
from pydantic import BaseModel

from airas.config.runner_type_info import RunnerType, runner_info_dict
from airas.features.create.fix_code_subgraph.prompt.code_fix_prompt import (
    code_fix_prompt,
)
from airas.services.api_client.llm_client.llm_facade_client import (
    LLM_MODEL,
    LLMFacadeClient,
)
from airas.types.research_hypothesis import ResearchHypothesis

logger = logging.getLogger(__name__)


class GenerateCodeForScripts(BaseModel):
    train_scripts_content: str
    evaluate_scripts_content: str
    preprocess_scripts_content: str
    main_scripts_content: str
    pyproject_toml_content: str
    config_yaml_content: str


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
    generated_file_contents: dict[str, str],
    experiment_iteration: int,
    runner_type: RunnerType,
    error_list: list[str],
    file_validations: dict[str, dict[str, list[str]]],
    prompt_template: str = code_fix_prompt,
    client: LLMFacadeClient | None = None,
) -> dict[str, dict[str, str] | list[str]]:
    client = client or LLMFacadeClient(llm_name=llm_name)

    data = {
        "generated_file_contents": generated_file_contents,
        "experiment_iteration": experiment_iteration,
        "new_method": new_method.model_dump(),
        "runner_type_prompt": runner_info_dict[runner_type]["prompt"],
        "error_list": error_list,  # Previous errors for analysis
        "file_validations": file_validations,  # Static validation results
    }
    env = Environment()
    template = env.from_string(prompt_template)
    messages = template.render(data)

    logger.info("Fixing code using LLM...")
    output, cost = client.structured_outputs(
        message=messages, data_model=GenerateCodeForScripts
    )
    if output is None:
        raise ValueError("Error: No response from LLM in fix_code.")

    file_mapping = {
        "train_scripts_content": "src/train.py",
        "evaluate_scripts_content": "src/evaluate.py",
        "preprocess_scripts_content": "src/preprocess.py",
        "main_scripts_content": "src/main.py",
        "pyproject_toml_content": "pyproject.toml",
        "config_yaml_content": "config/config.yaml",
    }

    for field, path in file_mapping.items():
        new_content = output.get(field)
        if _is_code_meaningful(new_content):
            generated_file_contents[path] = new_content

    # Only add experimental_results.error on first iteration (when no file_validations)
    if (
        not file_validations  # First iteration - no static validation yet
        and hasattr(new_method, "experimental_results")
        and new_method.experimental_results
        and new_method.experimental_results.error
    ):
        error_list.append(new_method.experimental_results.error)

    return {
        "generated_file_contents": generated_file_contents,
        "error_list": error_list[-3:],  # Keep only last 3 errors
    }
