import re
from logging import getLogger
from typing import Any

import bibtexparser
from jinja2 import Environment
from pydantic import BaseModel

from airas.services.api_client.llm_client.llm_facade_client import (
    LLM_MODEL,
    LLMFacadeClient,
)

logger = getLogger(__name__)


class LLMOutput(BaseModel):
    generated_html_text: str


def _parse_bibtex_to_dict(references_bib: str) -> dict[str, dict[str, Any]]:
    try:
        db = bibtexparser.loads(references_bib)
        references = {}
        for entry in db.entries:
            citation_key = entry.get("ID", "")
            if citation_key:
                references[citation_key] = entry
        return references
    except Exception as e:
        logger.warning(f"Failed to parse BibTeX: {e}")
        return {}


def _replace_citation_keys_with_links(
    html_text: str, references: dict[str, dict[str, Any]]
) -> str:
    def replace_citation(match):
        citation_key = match.group(1)
        if citation_key in references:
            ref = references[citation_key]
            if ref.get("arxiv_url"):
                link = ref["arxiv_url"]
            elif ref.get("doi"):
                link = f"https://doi.org/{ref['doi']}"
            elif ref.get("github_url"):
                link = ref["github_url"]
            else:
                link = f"#ref-{citation_key}"

            title = ref.get("title", citation_key)
            author = ref.get("author", "")
            if author:
                first_author = author.split(" and ")[0].split(",")[0].strip()
                display_text = f"({first_author}, {ref.get('year', 'n.d.')})"
            else:
                display_text = f"({citation_key})"

            return (
                f'<a href="{link}" target="_blank" title="{title}">{display_text}</a>'
            )
        else:
            logger.info(
                f"Citation key not found in references, ignoring: {citation_key}"
            )
            return ""

    citation_pattern = r"\[([^\[\],]+)\]"
    html_text = re.sub(citation_pattern, replace_citation, html_text)

    return html_text


def convert_to_html(
    llm_name: LLM_MODEL,
    paper_content: dict[str, str],
    image_file_name_list: list[str],
    references_bib: str,
    prompt_template: str,
    client: LLMFacadeClient | None = None,
) -> str:
    if client is None:
        client = LLMFacadeClient(llm_name=llm_name)

    references = _parse_bibtex_to_dict(references_bib)
    data = {
        "sections": [
            {"name": key, "content": paper_content[key]} for key in paper_content.keys()
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

    html_with_links = _replace_citation_keys_with_links(generated_html_text, references)

    return html_with_links
