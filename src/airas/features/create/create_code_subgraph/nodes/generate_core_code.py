import json
import logging

from jinja2 import Environment

from airas.config.runner_type_info import RunnerType, runner_info_dict
from airas.features.create.create_code_subgraph.prompt.generate_core_code_prompt import (
    generate_core_code_prompt,
)
from airas.services.api_client.llm_client.openai_client import (
    OPENAI_MODEL,
    OpenAIClient,
)
from airas.types.github import GitHubRepositoryInfo
from airas.types.research_hypothesis import ExperimentCode, ResearchHypothesis
from airas.utils.save_prompt import save_io_on_github

logger = logging.getLogger(__name__)


def generate_core_code(
    llm_name: OPENAI_MODEL,
    new_method: ResearchHypothesis,
    runner_type: RunnerType,
    secret_names: list[str],
    github_repository_info: GitHubRepositoryInfo,
    feedback_text: str | None = None,
    core_code_validation: tuple[bool, str] | None = None,
) -> ResearchHypothesis:
    client = OpenAIClient(reasoning_effort="high")
    env = Environment()

    template = env.from_string(generate_core_code_prompt)

    data = {
        "new_method": new_method.model_dump(),
        "runner_type_prompt": runner_info_dict[runner_type]["prompt"],
        "secret_names": secret_names,
        "consistency_feedback": feedback_text,
        "core_code_validation": core_code_validation,
    }
    messages = template.render(data)

    logger.info("Generating common experiment core logic using LLM...")

    output, cost = client.structured_outputs(
        model_name=llm_name,
        message=messages,
        data_model=ExperimentCode,
    )
    if output is None:
        raise ValueError("No response from LLM in generate_core_code.")

    save_io_on_github(
        github_repository_info=github_repository_info,
        input=messages,
        output=json.dumps(output, ensure_ascii=False, indent=4),
        subgraph_name="create_code_subgraph",
        node_name="generate_core_code",
    )

    new_method.experimental_design.experiment_core_code = ExperimentCode(**output)
    return new_method
