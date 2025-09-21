import json
from logging import getLogger

from jinja2 import Environment
from pydantic import BaseModel

from airas.services.api_client.llm_client.llm_facade_client import (
    LLM_MODEL,
    LLMFacadeClient,
)
from airas.types.github import GitHubRepositoryInfo
from airas.types.paper import PaperContent
from airas.utils.save_prompt import save_io_on_github

logger = getLogger(__name__)


class LLMOutput(BaseModel):
    was_experiment_executed: bool
    is_better_than_baseline: bool


def evaluate_paper_results(
    llm_name: LLM_MODEL,
    prompt_template: str,
    paper_content: PaperContent,
    github_repository_info: GitHubRepositoryInfo,
    client: LLMFacadeClient | None = None,
) -> tuple[bool, bool]:
    client = client or LLMFacadeClient(llm_name=llm_name)

    env = Environment()
    template = env.from_string(prompt_template)

    paper_data = paper_content.model_dump()
    data = {"paper_content": paper_data}

    messages = template.render(data)
    output, _cost = client.structured_outputs(message=messages, data_model=LLMOutput)

    if output is None:
        raise ValueError("No response from LLM in evaluate_paper_results node.")
    save_io_on_github(
        github_repository_info=github_repository_info,
        input=messages,
        output=json.dumps(output, ensure_ascii=False, indent=4),
        subgraph_name="evaluate_paper_results_subgraph",
        node_name="evaluate_paper_results",
    )
    return (
        output["was_experiment_executed"],
        output["is_better_than_baseline"],
    )
