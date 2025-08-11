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
from airas.types.research_study import ResearchStudy

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
    llm_name: LLM_MODEL,
    research_study_list: list[ResearchStudy],
    client: LLMFacadeClient | None = None,
) -> list[ResearchStudy]:
    if client is None:
        client = LLMFacadeClient(llm_name=llm_name)

    reference_research_study_list = []
    env = Environment()
    template = env.from_string(extract_reference_titles_prompt)

    for research_study in research_study_list:
        if not research_study.full_text:
            logger.warning(f"No full_text found for study: {research_study.title}")
            continue

        data = {"full_text": research_study.full_text}
        messages = template.render(data)

        try:
            output, cost = client.structured_outputs(
                message=messages, data_model=LLMOutput
            )
        except Exception as e:
            logger.error(
                f"Error extracting references for '{research_study.title}': {e}"
            )
            continue

        if output is None or not isinstance(output, dict):
            logger.warning(
                f"Warning: No valid response from LLM for reference extraction for '{research_study.title}'."
            )
            continue

        reference_titles = output.get("reference_titles", [])

        # Normalize and deduplicate titles
        unique_titles = []
        seen_normalized = set()

        for title in reference_titles:
            normalized_title = _normalize_title(title)
            if normalized_title not in seen_normalized:
                unique_titles.append(title)
                seen_normalized.add(normalized_title)

        # Create ResearchStudy objects for reference titles
        for title in unique_titles:
            reference_research_study_list.append(ResearchStudy(title=title))

        logger.info(
            f"Found {len(unique_titles)} unique reference titles for study '{research_study.title}'."
        )

    logger.info(f"Total reference studies found: {len(reference_research_study_list)}")
    return reference_research_study_list
