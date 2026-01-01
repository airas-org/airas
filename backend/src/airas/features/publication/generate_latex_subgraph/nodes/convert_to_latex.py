from logging import getLogger

from jinja2 import Environment

from airas.features.publication.generate_latex_subgraph.prompts.convert_to_latex_prompt import (
    convert_to_latex_prompt,
)
from airas.services.api_client.langchain_client import LangChainClient
from airas.services.api_client.llm_specs import LLM_MODELS
from airas.types.paper import PaperContent

logger = getLogger(__name__)


async def convert_to_latex(
    llm_name: LLM_MODELS,
    langchain_client: LangChainClient,
    paper_content: PaperContent,
    references_bib: str,
    latex_template_text: str | None = None,
    figures_dir: str = "images",
) -> PaperContent:
    env = Environment()

    data = {
        "figures_dir": figures_dir,
        "latex_template_text": latex_template_text,
        "references_bib": references_bib,
        "sections": [
            {"name": field, "content": getattr(paper_content, field)}
            for field in PaperContent.model_fields.keys()
            if getattr(paper_content, field)
        ],
    }

    env = Environment()
    template = env.from_string(convert_to_latex_prompt)
    messages = template.render(data)

    output = await langchain_client.structured_outputs(
        message=messages, data_model=PaperContent, llm_name=llm_name
    )
    if output is None:
        raise ValueError("Error: No response from the model in convert_to_latex.")

    return output
