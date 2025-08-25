from jinja2 import Environment
from pydantic import BaseModel

from airas.services.api_client.llm_client.llm_facade_client import (
    LLM_MODEL,
    LLMFacadeClient,
)
from airas.types.paper import PaperContent


class LLMOutput(BaseModel):
    generated_html_text: str


def convert_to_html(
    llm_name: LLM_MODEL,
    paper_content: PaperContent,
    image_file_name_list: list[str],
    prompt_template: str,
    client: LLMFacadeClient | None = None,
) -> str:
    """Convert paper content to HTML using LLM."""
    if client is None:
        client = LLMFacadeClient(llm_name=llm_name)

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

    if not isinstance(output, dict):
        raise ValueError("Invalid output format")

    generated_html_text = output.get("generated_html_text", "")
    if not generated_html_text:
        raise ValueError("Missing or empty 'generated_html_text' in output.")

    return generated_html_text
