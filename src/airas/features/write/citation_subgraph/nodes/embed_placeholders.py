import re
from collections import defaultdict
from itertools import count
from logging import getLogger

from jinja2 import Environment

from airas.services.api_client.llm_client.llm_facade_client import (
    LLM_MODEL,
    LLMFacadeClient,
)
from airas.types.research_study import PaperBody

logger = getLogger(__name__)

_PLACEHOLDER_COUNTERS: dict[str, count] = defaultdict(lambda: count(1))


def _replace_underscores_in_keys(paper_dict: dict[str, str]) -> dict[str, str]:
    return {key.replace("_", " "): value for key, value in paper_dict.items()}


def _assign_placeholder_ids(text: str, placeholder: str) -> tuple[str, list[str]]:
    pattern = re.escape(placeholder)
    counter = _PLACEHOLDER_COUNTERS[placeholder]
    placeholder_ids = []

    def replacer(_: re.Match) -> str:
        new_id = f"{placeholder[:-2]}_{next(counter)}]]"
        placeholder_ids.append(new_id)
        return new_id

    new_text = re.sub(pattern, replacer, text)
    return new_text, placeholder_ids


def embed_placeholders(
    llm_name: LLM_MODEL,
    paper_content: PaperBody,
    prompt_template: str,
    placeholder: str = "[[CITATION]]",
    client: LLMFacadeClient | None = None,
) -> tuple[PaperBody, list[str]]:
    if client is None:
        client = LLMFacadeClient(llm_name=llm_name)

    data = {
        "sections": [
            {"name": section, "content": paper_content.section}
            for section in paper_content.model_fields.keys()
        ],
        "placeholder": placeholder,
    }

    env = Environment()
    template = env.from_string(prompt_template)
    messages = template.render(data)

    try:
        # TODO: Add error handling if none of the placeholders are embedded
        output, cost = client.structured_outputs(
            message=messages,
            data_model=PaperBody,
        )
        output = _replace_underscores_in_keys(output)

        paper_content_with_placeholders = {}
        all_placeholders = []

        for section, text in output.items():
            new_text, ids = _assign_placeholder_ids(text, placeholder)
            paper_content_with_placeholders[section] = new_text
            all_placeholders.extend(ids)

        return paper_content_with_placeholders, all_placeholders

    except Exception as e:
        logger.warning(f"embed_placeholders failed, returning original content: {e}")

    return paper_content, []
