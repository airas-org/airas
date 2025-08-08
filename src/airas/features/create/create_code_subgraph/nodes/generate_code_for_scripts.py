import json
import logging

from jinja2 import Environment
from pydantic import BaseModel

from airas.features.create.create_code_subgraph.input_data import (
    create_code_subgraph_input_data,
)
from airas.features.create.create_code_subgraph.prompt.generate_code_for_scripts import (
    generate_code_for_scripts_prompt,
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


def generate_code_for_scripts(
    llm_name: LLM_MODEL,
    new_method: str,
    experiment_code: str,
    experiment_iteration: int,
    prompt_template: str = generate_code_for_scripts_prompt,
    client: LLMFacadeClient | None = None,
) -> dict[str, str]:
    """Generate code files using LLM based on new method and experiment code"""

    client = client or LLMFacadeClient(llm_name=llm_name)

    # Prepare template data
    data = {
        "new_method": new_method,
        "experiment_code": experiment_code,
        "experiment_iteration": experiment_iteration,
    }

    env = Environment()
    template = env.from_string(prompt_template)
    messages = template.render(data)

    logger.info("Generating code files using LLM...")

    output, cost = client.structured_outputs(
        message=messages, data_model=GenerateCodeForScripts
    )
    if output is None:
        raise ValueError("Error: No response from LLM in generate_code_for_scripts.")
    return {
        "src/train.py": output["train_scripts_content"],
        "src/evaluate.py": output["evaluate_scripts_content"],
        "src/preprocess.py": output["preprocess_scripts_content"],
        "src/main.py": output["main_scripts_content"],
        "requirements.txt": output["requirements_txt_content"],
        "config/config.yaml": output["config_yaml_content"],
    }


if __name__ == "__main__":
    llm_name = "gpt-4o-mini-2024-07-18"
    new_method = create_code_subgraph_input_data["new_method"]
    experiment_code = create_code_subgraph_input_data["experiment_code"]
    experiment_iteration = 1

    result = generate_code_for_scripts(
        llm_name=llm_name,
        new_method=new_method,
        experiment_code=experiment_code,
        experiment_iteration=experiment_iteration,
    )
    print(json.dumps(result, indent=2))
