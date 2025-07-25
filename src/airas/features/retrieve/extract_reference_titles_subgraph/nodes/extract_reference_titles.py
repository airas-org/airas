import string
from logging import getLogger

from jinja2 import Environment
from pydantic import BaseModel

from airas.features.retrieve.extract_reference_titles_subgraph.prompts.extract_reference_titles_prompt import (
    extract_reference_titles_prompt,
)
from airas.services.api_client.llm_client.llm_facade_client import (
    LLM_MODEL,
    LLMFacadeClient,
)

logger = getLogger(__name__)


class LLMOutput(BaseModel):
    reference_titles: list[str]


# Possible to extract from different parts of the paper
def _normalize_title(title: str) -> str:
    normalized = title.lower()
    translator = str.maketrans("", "", string.punctuation)
    normalized = normalized.translate(translator)
    normalized = "".join(normalized.split())

    return normalized


def extract_reference_titles(
    full_text: str,
    llm_name: LLM_MODEL,
    client: LLMFacadeClient | None = None,
) -> list[str]:
    if client is None:
        client = LLMFacadeClient(llm_name=llm_name)

    env = Environment()
    template = env.from_string(extract_reference_titles_prompt)
    data = {"full_text": full_text}
    messages = template.render(data)

    try:
        output, cost = client.structured_outputs(message=messages, data_model=LLMOutput)
    except Exception as e:
        logger.error(f"Error extracting references: {e}")
        return []

    if output is None or not isinstance(output, dict):
        logger.warning("Warning: No valid response from LLM for reference extraction.")
        return []

    reference_titles = output.get("reference_titles", [])

    unique_titles = []
    seen_normalized = set()

    for title in reference_titles:
        normalized_title = _normalize_title(title)
        if normalized_title not in seen_normalized:
            unique_titles.append(title)
            seen_normalized.add(normalized_title)

    logger.info(f"Found {len(unique_titles)} unique titles after normalization.")
    return unique_titles
