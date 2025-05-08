from logging import getLogger

from jinja2 import Environment
from pydantic import BaseModel

from airas.publication.html_subgraph.prompt.convert_to_html_prompt import (
    convert_to_html_prompt,
)
from airas.utils.api_client.llm_facade_client import LLM_MODEL, LLMFacadeClient

logger = getLogger(__name__)


class LLMOutput(BaseModel):
    generated_html_text: str


def convert_to_html(
    llm_name: LLM_MODEL,
    paper_content: dict[str, str],
    client: LLMFacadeClient | None = None, 
) -> str:
    if client is None:
        client = LLMFacadeClient(llm_name=llm_name)

    data = {
        "sections": [
            {"name": section, "content": paper_content[section]}
            for section in paper_content.keys()
        ]
    }

    env = Environment()
    template = env.from_string(convert_to_html_prompt)
    messages = template.render(data)
    output, cost = client.structured_outputs(
        message=messages,
        data_model=LLMOutput,
    )
    if output is None:
        raise ValueError("No response from the model in convert_to_html.")
    if not isinstance(output, dict) or not output:
        raise ValueError("Empty HTML content")
    if "generated_html_text" in output:
        generated_html_text = output["generated_html_text"]
        if not generated_html_text:
            raise ValueError("Empty HTML content")
        return generated_html_text
    else:
        raise ValueError("Error: No response from the model in convert_to_html.")
