from logging import getLogger

from jinja2 import Environment

from airas.features.publication.latex_subgraph.prompt.convert_to_latex_prompt import (
    convert_to_latex_prompt,
)
from airas.services.api_client.llm_client.llm_facade_client import (
    LLM_MODEL,
    LLMFacadeClient,
)
from airas.types.paper import PaperContent

logger = getLogger(__name__)


def convert_to_latex_str(
    llm_name: LLM_MODEL,
    paper_content: PaperContent,
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

    missing_fields = [
        field
        for field in PaperContent.model_fields
        if field not in output or not output[field].strip()
    ]
    if missing_fields:
        raise ValueError(f"Missing or empty fields in model response: {missing_fields}")

    return PaperContent(**output)
