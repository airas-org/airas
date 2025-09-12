import logging

from jinja2 import Environment
from pydantic import BaseModel

from airas.config.runner_type_info import RunnerType, runner_info_dict
from airas.features.create.create_code_subgraph.prompt.convert_code_to_scripts_prompt import (
    convert_code_to_scripts_prompt,
)
from airas.services.api_client.llm_client.llm_facade_client import (
    LLM_MODEL,
    LLMFacadeClient,
)
from airas.types.research_hypothesis import ResearchHypothesis

logger = logging.getLogger(__name__)


class ConvertCodeToScripts(BaseModel):
    train_scripts_content: str
    evaluate_scripts_content: str
    preprocess_scripts_content: str
    main_scripts_content: str
    pyproject_toml_content: str
    smoke_test_yaml_content: str
    full_experiment_yaml_content: str


def convert_code_to_scripts(
    llm_name: LLM_MODEL,
    new_method: ResearchHypothesis,
    experiment_iteration: int,
    runner_type: RunnerType,
    secret_names: list[str],
    file_validations: dict[str, dict[str, list[str]]],
    prompt_template: str = convert_code_to_scripts_prompt,
    client: LLMFacadeClient | None = None,
    generated_file_contents: dict[str, str] | None = None,
) -> dict[str, str]:
    client = client or LLMFacadeClient(llm_name=llm_name)

    data = {
        "runner_type_prompt": runner_info_dict[runner_type]["prompt"],
        "new_method": new_method.model_dump(),
        "experiment_iteration": experiment_iteration,
        "secret_names": secret_names,
        "file_validations": file_validations,
        "generated_file_contents": generated_file_contents,
    }

    env = Environment()
    template = env.from_string(prompt_template)
    messages = template.render(data)

    logger.info("Converting experiment code to script files using LLM...")

    output, cost = client.structured_outputs(
        message=messages, data_model=ConvertCodeToScripts
    )
    if output is None:
        raise ValueError("Error: No response from LLM in convert_code_to_scripts.")
    return {
        "src/train.py": output["train_scripts_content"],
        "src/evaluate.py": output["evaluate_scripts_content"],
        "src/preprocess.py": output["preprocess_scripts_content"],
        "src/main.py": output["main_scripts_content"],
        "pyproject.toml": output["pyproject_toml_content"],
        "config/smoke_test.yaml": output["smoke_test_yaml_content"],
        "config/full_experiment.yaml": output["full_experiment_yaml_content"],
    }
