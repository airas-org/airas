import json

from jinja2 import Environment
from pydantic import BaseModel

from airas.services.api_client.llm_client.llm_facade_client import (
    LLM_MODEL,
    LLMFacadeClient,
)
from airas.types.github import GitHubRepositoryInfo
from airas.types.paper import PaperContent
from airas.types.research_hypothesis import ResearchHypothesis
from airas.utils.save_prompt import save_io_on_github


class LLMOutput(BaseModel):
    generated_html_text: str


def convert_to_html(
    llm_name: LLM_MODEL,
    paper_content: PaperContent,
    new_method: ResearchHypothesis,
    prompt_template: str,
    github_repository_info: GitHubRepositoryInfo,
    client: LLMFacadeClient | None = None,
) -> str:
    """Convert paper content to HTML using LLM."""
    if client is None:
        client = LLMFacadeClient(llm_name=llm_name)

    # Extract image files from new_method
    image_file_name_list = []
    if new_method.experiment_runs:
        for run in new_method.experiment_runs:
            if run.results and run.results.figures:
                image_file_name_list.extend(run.results.figures)
    if (
        new_method.experimental_analysis
        and new_method.experimental_analysis.comparison_figures
    ):
        image_file_name_list.extend(new_method.experimental_analysis.comparison_figures)

    data = {
        "sections": [
            {"name": field, "content": getattr(paper_content, field)}
            for field in PaperContent.model_fields.keys()
            if getattr(paper_content, field)
        ],
        "image_file_name_list": image_file_name_list,
    }

    env = Environment()
    template = env.from_string(prompt_template)
    messages = template.render(data)

    output, _ = client.structured_outputs(
        message=messages,
        data_model=LLMOutput,
    )
    if output is None:
        raise ValueError("No response from the model in convert_to_html.")
    save_io_on_github(
        github_repository_info=github_repository_info,
        input=messages,
        output=json.dumps(output, ensure_ascii=False, indent=4),
        subgraph_name="html_subgraph",
        node_name="convert_to_html",
        llm_name=llm_name,
    )

    generated_html_text = output.get("generated_html_text", "")
    if not generated_html_text:
        raise ValueError("Missing or empty 'generated_html_text' in output.")

    return generated_html_text
