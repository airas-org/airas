import json
from logging import getLogger

from jinja2 import Environment
from pydantic import BaseModel

from airas.features.create.create_code_subgraph.prompt.validate_base_code_prompt import (
    validate_base_code_prompt,
)
from airas.services.api_client.llm_client.llm_facade_client import (
    LLM_MODEL,
    LLMFacadeClient,
)
from airas.types.github import GitHubRepositoryInfo
from airas.types.research_hypothesis import ResearchHypothesis
from airas.utils.save_prompt import save_io_on_github

logger = getLogger(__name__)


class ValidationOutput(BaseModel):
    is_base_code_ready: bool
    base_code_issue: str


def validate_base_code(
    llm_name: LLM_MODEL,
    new_method: ResearchHypothesis,
    github_repository_info: GitHubRepositoryInfo,
    experiment_iteration: int,
    prompt_template: str = validate_base_code_prompt,
    llm_client: LLMFacadeClient | None = None,
) -> tuple[bool, str]:
    client = llm_client or LLMFacadeClient(llm_name=llm_name)
    env = Environment()
    template = env.from_string(prompt_template)

    messages = template.render(
        {
            "new_method": new_method.model_dump(),
            "experiment_iteration": experiment_iteration,
        }
    )
    output, _ = client.structured_outputs(message=messages, data_model=ValidationOutput)

    if output is None:
        logger.error("No response from LLM in validate_base_code. Defaulting to False.")
        return False, ""

    save_io_on_github(
        github_repository_info=github_repository_info,
        input=messages,
        output=json.dumps(output, ensure_ascii=False, indent=4),
        subgraph_name="create_code_subgraph",
        node_name="validate_base_code",
    )

    return output["is_base_code_ready"], output["base_code_issue"]
