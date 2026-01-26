from jinja2 import Environment
from pydantic import BaseModel

from airas.core.types.paper import PaperContent
from airas.core.types.research_session import ResearchSession
from airas.infra.langchain_client import LangChainClient
from airas.infra.llm_specs import LLM_MODELS


class LLMOutput(BaseModel):
    generated_html_text: str


async def convert_to_html(
    llm_name: LLM_MODELS,
    paper_content: PaperContent,
    research_session: ResearchSession,
    prompt_template: str,
    llm_client: LangChainClient,
) -> str:
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

    output = await llm_client.structured_outputs(
        llm_name=llm_name, message=messages, data_model=LLMOutput
    )
    if output is None:
        raise ValueError("No response from the model in convert_to_html.")

    if not (generated_html_text := output.get("generated_html_text", "")):
        raise ValueError("Missing or empty 'generated_html_text' in output.")

    return generated_html_text
