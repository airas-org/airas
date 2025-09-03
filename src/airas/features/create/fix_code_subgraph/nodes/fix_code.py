import logging

from jinja2 import Environment
from pydantic import BaseModel

from airas.config.runtime_prompt import RuntimeKeyType, runtime_prompt_dict
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
    requirements_txt_content: str
    config_yaml_content: str


def _is_code_meaningful(content: str | None) -> bool:
    if not content or not content.strip():
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
    current_files: dict[str, str],
    experiment_iteration: int,
    runtime_name: RuntimeKeyType,
    prompt_template: str = code_fix_prompt,
    client: LLMFacadeClient | None = None,
) -> dict[str, str]:
    client = client or LLMFacadeClient(llm_name=llm_name)

    data = {
        "current_files": current_files,
        "experiment_iteration": experiment_iteration,
        "new_method": new_method.model_dump(),
        "runtime_prompt": runtime_prompt_dict[runtime_name],
    }
    env = Environment()
    template = env.from_string(prompt_template)
    messages = template.render(data)

    logger.info("Analyzing errors and generating fixed code using LLM...")
    output, cost = client.structured_outputs(
        message=messages, data_model=GenerateCodeForScripts
    )
    if output is None:
        raise ValueError("Error: No response from LLM in fix_code.")

    updated_files = current_files.copy()

    file_mapping = {
        "train_scripts_content": "src/train.py",
        "evaluate_scripts_content": "src/evaluate.py",
        "preprocess_scripts_content": "src/preprocess.py",
        "main_scripts_content": "src/main.py",
        "requirements_txt_content": "requirements.txt",
        "config_yaml_content": "config/config.yaml",
    }

    for field, path in file_mapping.items():
        new_content = output.get(field)
        if _is_code_meaningful(new_content):
            updated_files[path] = new_content

    return updated_files
