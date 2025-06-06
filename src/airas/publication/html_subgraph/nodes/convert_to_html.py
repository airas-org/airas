import re
from logging import getLogger
from typing import Any

from jinja2 import Environment
from pydantic import BaseModel

from airas.utils.api_client.llm_facade_client import LLM_MODEL, LLMFacadeClient

logger = getLogger(__name__)


class LLMOutput(BaseModel):
    generated_html_text: str


def _replace_placeholders(
    html_text: str,
    references: dict[str, dict[str, Any]],
) -> str:
    for i, (placeholder, ref) in enumerate(references.items()):

        link = ref.get("doi") or ref.get("id") or "#"
        display_text = f"[{i + 1}]"
        anchor = f'<a href="{link}" target="_blank">{display_text}</a>'
        html_text = html_text.replace(placeholder, anchor)

    return html_text
    
def convert_to_html(
    llm_name: LLM_MODEL,
    prompt_template: str, 
    paper_content_with_placeholders: dict[str, str],
    references: dict[str, dict[str, Any]], 
    client: LLMFacadeClient | None = None, 
) -> str:
    if client is None:
        client = LLMFacadeClient(llm_name=llm_name)

    data = {
        "sections": [
            {"name": section, "content": paper_content_with_placeholders[section]}
            for section in paper_content_with_placeholders.keys()
        ]
    }

    env = Environment()
    template = env.from_string(prompt_template)
    messages = template.render(data)
    output, cost = client.structured_outputs(
        message=messages,
        data_model=LLMOutput,
    )
    if output is None:
        raise ValueError("No response from the model in convert_to_html.")
    
    if not isinstance(output, dict) :
        raise ValueError("Empty HTML content")
    
    generated_html_text = output["generated_html_text"]
    if not generated_html_text:
        raise ValueError("Missing or empty 'generated_html_text' in output.")

    return _replace_placeholders(generated_html_text, references)