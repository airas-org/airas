import json
from logging import getLogger

from jinja2 import Environment
from pydantic import BaseModel

from airas.features.publication.latex_subgraph.prompt.fix_latex_text_prompt import (
    fix_latex_text_prompt,
)
from airas.services.api_client.llm_client.llm_facade_client import (
    LLM_MODEL,
    LLMFacadeClient,
)
from airas.types.github import GitHubRepositoryInfo
from airas.utils.save_prompt import save_io_on_github

logger = getLogger(__name__)


class LLMOutput(BaseModel):
    latex_text: str


def fix_latex_text(
    llm_name: LLM_MODEL,
    latex_text: str,
    latex_error_text: str,
    github_repository_info: GitHubRepositoryInfo,
    node_name: str,
    client: LLMFacadeClient | None = None,
) -> str:
    client = client or LLMFacadeClient(llm_name=llm_name)

    data = {"latex_text": latex_text, "latex_error_text": latex_error_text}

    env = Environment()
    template = env.from_string(fix_latex_text_prompt)
    messages = template.render(data)
    output, cost = client.structured_outputs(
        message=messages,
        data_model=LLMOutput,
    )
    if output is None:
        raise ValueError("Error: No response from LLM in fix_latex_text.")
    save_io_on_github(
        github_repository_info=github_repository_info,
        input=messages,
        output=json.dumps(output, ensure_ascii=False, indent=4),
        subgraph_name="latex_subgraph",
        node_name=node_name,
        llm_name=llm_name,
    )
    latex_text = output["latex_text"]
    return latex_text


# if __name__ == "__main__":
#     llm_name = "gpt-4o-mini-2024-07-18"
#     output_text_data = "No error"
#     error_text_data = "Error"
#     result = fix_latex_text(llm_name, output_text_data, error_text_data)
#     print(result)
