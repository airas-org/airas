import json
from logging import getLogger

from jinja2 import Environment
from pydantic import BaseModel

from airas.features.execution.github_actions_executor_subgraph.prompt.extract_required_info_prompt import (
    extract_required_info_prompt,
)
from airas.services.api_client.llm_client.llm_facade_client import (
    LLM_MODEL,
    LLMFacadeClient,
)
from airas.types.github import GitHubRepositoryInfo
from airas.utils.save_prompt import save_io_on_github

logger = getLogger(__name__)


class LLMOutput(BaseModel):
    extracted_output: str
    extracted_error: str


def extract_required_info(
    llm_name: LLM_MODEL,
    output_text_data: str,
    error_text_data: str,
    github_repository_info: GitHubRepositoryInfo,
    client: LLMFacadeClient | None = None,
) -> tuple[str, str]:
    client = client or LLMFacadeClient(llm_name=llm_name)
    env = Environment()
    template = env.from_string(extract_required_info_prompt)
    data = {
        "output_text_data": output_text_data,
        "error_text_data": error_text_data,
    }
    messages = template.render(data)
    output, cost = client.structured_outputs(
        message=messages,
        data_model=LLMOutput,
    )
    if output is None:
        raise ValueError("No response from LLM in idea_generator.")
    save_io_on_github(
        github_repository_info=github_repository_info,
        input=messages,
        output=json.dumps(output, ensure_ascii=False, indent=4),
        subgraph_name="github_actions_executor_subgraph",
        node_name="extract_required_info",
        llm_name=llm_name,
    )
    return output["extracted_output"], output["extracted_error"]
