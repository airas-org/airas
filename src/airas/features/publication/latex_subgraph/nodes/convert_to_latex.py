import json
from logging import getLogger

from jinja2 import Environment

from airas.features.publication.latex_subgraph.prompt.convert_to_latex_prompt import (
    convert_to_latex_prompt,
)
from airas.services.api_client.llm_client.llm_facade_client import (
    LLM_MODEL,
    LLMFacadeClient,
)
from airas.types.github import GitHubRepositoryInfo
from airas.types.paper import PaperContent
from airas.utils.save_prompt import save_io_on_github

logger = getLogger(__name__)


def convert_to_latex_str(
    llm_name: LLM_MODEL,
    paper_content: PaperContent,
    github_repository_info: GitHubRepositoryInfo,
    figures_dir: str = "images",
    client: LLMFacadeClient | None = None,
) -> PaperContent:
    client = client or LLMFacadeClient(llm_name)
    env = Environment()

    data = {
        "figures_dir": figures_dir,
        "sections": [
            {"name": field, "content": getattr(paper_content, field)}
            for field in PaperContent.model_fields.keys()
            if getattr(paper_content, field)
        ],
        # "citation_placeholders": references_bib,
    }

    env = Environment()
    template = env.from_string(convert_to_latex_prompt)
    messages = template.render(data)

    output, cost = client.structured_outputs(
        message=messages,
        data_model=PaperContent,
    )
    if output is None:
        raise ValueError("Error: No response from the model in convert_to_latex.")
    save_io_on_github(
        github_repository_info=github_repository_info,
        input=messages,
        output=json.dumps(output, ensure_ascii=False, indent=4),
        subgraph_name="latex_subgraph",
        node_name="convert_to_latex_str",
        llm_name=llm_name,
    )
    missing_fields = [
        field
        for field in PaperContent.model_fields
        if field not in output or not output[field].strip()
    ]
    if missing_fields:
        raise ValueError(f"Missing or empty fields in model response: {missing_fields}")

    return PaperContent(**output)
