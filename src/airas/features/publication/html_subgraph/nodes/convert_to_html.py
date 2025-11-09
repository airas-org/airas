from dependency_injector import providers
from dependency_injector.wiring import Provide, inject
from jinja2 import Environment
from pydantic import BaseModel

from airas.services.api_client.api_clients_container import SyncContainer
from airas.services.api_client.llm_client.llm_facade_client import (
    LLM_MODEL,
    LLMFacadeClient,
)
from airas.types.paper import PaperContent
from airas.types.research_session import ResearchSession


class LLMOutput(BaseModel):
    generated_html_text: str


@inject
def convert_to_html(
    llm_name: LLM_MODEL,
    paper_content: PaperContent,
    research_session: ResearchSession,
    prompt_template: str,
    llm_facade_provider: providers.Factory[LLMFacadeClient] = Provide[
        SyncContainer.llm_facade_provider
    ],
) -> str:
    client = llm_facade_provider(llm_name=llm_name)

    image_file_name_list: list[str] = []

    if not (best_iter := research_session.best_iteration):
        return ""

    image_file_name_list.extend(
        fig
        for run in best_iter.experiment_runs or []
        for fig in getattr(run.results, "figures", []) or []
    )

    image_file_name_list.extend(
        getattr(best_iter.experimental_analysis, "comparison_figures", []) or []
    )

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

    if not (generated_html_text := output.get("generated_html_text", "")):
        raise ValueError("Missing or empty 'generated_html_text' in output.")

    return generated_html_text
