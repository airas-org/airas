from logging import getLogger

from jinja2 import Environment

from airas.core.llm_config import NodeLLMConfig
from airas.core.types.paper import BasePaperContent, PaperContent
from airas.infra.langchain_client import LangChainClient
from airas.usecases.publication.generate_latex_subgraph.prompts.convert_to_latex_prompt import (
    convert_to_latex_prompt,
)

logger = getLogger(__name__)


async def convert_to_latex(
    llm_config: NodeLLMConfig,
    langchain_client: LangChainClient,
    paper_content: PaperContent,
    references_bib: str,
    latex_template_text: str | None = None,
    figures_dir: str = "images",
    paper_content_model: type[BasePaperContent],
) -> PaperContent:
    env = Environment()

    data = {
        "figures_dir": figures_dir,
        "latex_template_text": latex_template_text,
        "references_bib": references_bib,
        "sections": [
            {"name": field, "content": getattr(paper_content, field)}
            for field in paper_content_model.model_fields.keys()
            if getattr(paper_content, field)
        ],
    }

    env = Environment()
    template = env.from_string(convert_to_latex_prompt)
    messages = template.render(data)

    output = await langchain_client.structured_outputs(
        message=messages,
        data_model=paper_content_model,
        llm_name=llm_config.llm_name,
        params=llm_config.params,
    )
    if output is None:
        raise ValueError("Error: No response from the model in convert_to_latex.")

    return output
