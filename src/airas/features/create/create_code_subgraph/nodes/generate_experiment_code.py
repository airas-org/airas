import json
import logging

from jinja2 import Environment

from airas.config.runner_type_info import RunnerType, runner_info_dict
from airas.features.create.create_code_subgraph.prompt.generate_experiment_code_prompt import (
    generate_experiment_code_prompt,
)
from airas.services.api_client.llm_client.openai_client import (
    OPENAI_MODEL,
    OpenAIClient,
)
from airas.types.github import GitHubRepositoryInfo
from airas.types.research_iteration import ExperimentCode
from airas.types.research_session import ResearchSession
from airas.types.wandb import WandbInfo
from airas.utils.save_prompt import save_io_on_github

logger = logging.getLogger(__name__)


def generate_experiment_code(
    llm_name: OPENAI_MODEL,
    research_session: ResearchSession,
    runner_type: RunnerType,
    github_repository_info: GitHubRepositoryInfo,
    wandb_info: WandbInfo | None = None,
    code_validation: tuple[bool, str] | None = None,
) -> ExperimentCode:
    client = OpenAIClient(reasoning_effort="high")
    env = Environment()
    template = env.from_string(generate_experiment_code_prompt)

    data = {
        "research_session": research_session,
        "runner_type_prompt": runner_info_dict[runner_type]["prompt"],
        "code_validation": code_validation,
        "wandb_info": wandb_info.model_dump() if wandb_info else None,
    }
    messages = template.render(data)

    output, _ = client.structured_outputs(
        model_name=llm_name,
        message=messages,
        data_model=ExperimentCode,
    )
    if output is None:
        raise ValueError("No response from LLM in generate_experiment_code.")

    save_io_on_github(
        github_repository_info=github_repository_info,
        input=messages,
        output=json.dumps(output, ensure_ascii=False, indent=4),
        subgraph_name="create_code_subgraph",
        node_name="generate_experiment_code",
        llm_name=llm_name,
    )

    return ExperimentCode(**output)
