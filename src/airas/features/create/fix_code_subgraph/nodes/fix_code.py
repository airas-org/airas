import json
import logging

from jinja2 import Environment
from pydantic import BaseModel

from airas.features.create.fix_code_subgraph.prompt.code_fix_prompt import (
    code_fix_prompt,
)
from airas.services.api_client.llm_client.llm_facade_client import (
    LLM_MODEL,
    LLMFacadeClient,
)

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
    output_text_data: str,
    error_text_data: str,
    current_files: dict[str, str],
    experiment_iteration: int,
    prompt_template: str = code_fix_prompt,
    client: LLMFacadeClient | None = None,
) -> dict[str, str]:
    """Analyze errors and generate fixed code using LLM"""
    client = client or LLMFacadeClient(llm_name=llm_name)

    # Prepare template data
    data = {
        "output_text_data": output_text_data,
        "error_text_data": error_text_data,
        "current_files": current_files,
        "experiment_iteration": experiment_iteration,
    }

    # Render prompt template
    env = Environment()
    template = env.from_string(prompt_template)
    messages = template.render(data)

    logger.info("Analyzing errors and generating fixed code using LLM...")
    output, cost = client.structured_outputs(
        message=messages, data_model=GenerateCodeForScripts
    )
    if output is None:
        raise ValueError("Error: No response from LLM in fix_code.")

    # This preserves any files not touched by the LLM and prevents blanking.
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


def should_fix_code(output_text_data: str, error_text_data: str) -> bool:
    """Determine if code needs fixing based on error data"""

    # If there are clear error indicators, we should fix
    error_indicators = [
        "Error:",
        "Exception:",
        "Traceback",
        "ImportError",
        "ModuleNotFoundError",
        "SyntaxError",
        "NameError",
        "AttributeError",
        "TypeError",
        "ValueError",
        "FileNotFoundError",
    ]

    # Check if error_text_data contains actual errors
    if error_text_data and error_text_data.strip():
        for indicator in error_indicators:
            if indicator in error_text_data:
                return True

    # If both output and error are empty, something went wrong
    if not output_text_data.strip() and not error_text_data.strip():
        return True

    # If output contains error messages
    if output_text_data:
        for indicator in error_indicators:
            if indicator in output_text_data:
                return True

    # Otherwise, assume it's working
    return False


if __name__ == "__main__":
    llm_name = "gpt-4o-mini-2024-07-18"
    output_text_data = "Process started..."
    error_text_data = "ImportError: No module named 'numpy'"
    current_files = {
        "src/main.py": "import numpy as np\nprint('Hello')",
        "requirements.txt": "pandas==1.3.0",
    }

    # Test should_fix_code
    should_fix = should_fix_code(output_text_data, error_text_data)
    print(f"Should fix code: {should_fix}")

    if should_fix:
        result = fix_code(
            llm_name=llm_name,
            output_text_data=output_text_data,
            error_text_data=error_text_data,
            current_files=current_files,
            prompt_template=code_fix_prompt,
        )
        print(json.dumps(result, indent=2))
