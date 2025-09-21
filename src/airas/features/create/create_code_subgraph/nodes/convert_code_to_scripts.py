import json
import logging

from jinja2 import Environment

from airas.config.runner_type_info import RunnerType, runner_info_dict
from airas.features.create.create_code_subgraph.prompt.convert_code_to_scripts_prompt import (
    convert_code_to_scripts_prompt,
)
from airas.services.api_client.llm_client.llm_facade_client import (
    LLM_MODEL,
    LLMFacadeClient,
)
from airas.types.github import GitHubRepositoryInfo
from airas.types.research_hypothesis import ExperimentCode, ResearchHypothesis
from airas.utils.save_prompt import save_io_on_github

logger = logging.getLogger(__name__)


def convert_code_to_scripts(
    llm_name: LLM_MODEL,
    experiment_code_str: str,
    new_method: ResearchHypothesis,
    experiment_iteration: int,
    runner_type: RunnerType,
    secret_names: list[str],
    file_static_validations: dict[str, dict[str, list[str]]],
    github_repository_info: GitHubRepositoryInfo,
    prompt_template: str = convert_code_to_scripts_prompt,
    client: LLMFacadeClient | None = None,
) -> ResearchHypothesis:
    client = client or LLMFacadeClient(llm_name=llm_name)

    data = {
        "runner_type_prompt": runner_info_dict[runner_type]["prompt"],
        "experiment_code_str": experiment_code_str,
        "new_method": new_method.model_dump(),
        "experiment_iteration": experiment_iteration,
        "secret_names": secret_names,
        "file_static_validations": file_static_validations,
    }

    env = Environment()
    template = env.from_string(prompt_template)
    messages = template.render(data)

    logger.info("Converting experiment code to script files using LLM...")

    output, cost = client.structured_outputs(
        message=messages, data_model=ExperimentCode
    )
    if output is None:
        raise ValueError("Error: No response from LLM in convert_code_to_scripts.")
    save_io_on_github(
        github_repository_info=github_repository_info,
        input=messages,
        output=json.dumps(output, ensure_ascii=False, indent=4),
        subgraph_name="create_code_subgraph",
        node_name="convert_code_to_scripts",
    )
    new_method.experimental_design.experiment_code = ExperimentCode(**output)

    return new_method
