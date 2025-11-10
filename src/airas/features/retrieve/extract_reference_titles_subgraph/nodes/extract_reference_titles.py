import asyncio
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


async def _extract_references_from_study(
    research_study: ResearchStudy,
    template: str,
    client: LLMFacadeClient,
    llm_name: LLM_MODEL,
) -> list[str]:
    if not research_study.full_text:
        logger.warning(f"No full_text found for study: {research_study.title}")
        return []

    env = Environment()
    jinja_template = env.from_string(template)
    data = {"full_text": research_study.full_text}
    messages = jinja_template.render(data)

    try:
        output, _ = await client.structured_outputs(
            message=messages,
            data_model=LLMOutput,
            llm_name=llm_name,
        )
    except Exception as e:
        logger.error(f"Error extracting references for '{research_study.title}': {e}")
        return []

    if output is None or not isinstance(output, dict):
        logger.warning(
            f"Warning: No valid response from LLM for reference extraction for '{research_study.title}'."
        )
        return []
    reference_titles = output.get("reference_titles", [])
    logger.info(
        f"Found {len(reference_titles)} reference titles for study '{research_study.title}'."
    )

    return reference_titles


async def extract_reference_titles(
    llm_name: LLM_MODEL,
    research_study_list: list[ResearchStudy],
    client: LLMFacadeClient | None = None,
) -> list[ResearchStudy]:
    client = client or LLMFacadeClient(llm_name=llm_name)

    valid_studies = [
        research_study
        for research_study in research_study_list
        if research_study.full_text
    ]
    if not valid_studies:
        logger.warning("No studies with full_text found")
        return []

    # NOTE: Using multithreading for easier implementation, though async is more efficient.
    # with ThreadPoolExecutor(max_workers=max_workers) as executor:
    #     future_to_study = {
    #         executor.submit(
    #             _extract_references_from_study,
    #             study,
    #             extract_reference_titles_prompt,
    #             github_repository_info,
    #             index,
    #             client,
    #             llm_name,
    #         ): study
    #         for index, study in enumerate(valid_studies)
    #     }

    #     for future in as_completed(future_to_study):
    #         study = future_to_study[future]
    #         try:
    #             titles = future.result()
    #             all_reference_titles.extend(titles)
    #         except Exception as e:
    #             logger.error(f"Error processing study '{study.title}': {e}")

    # Global deduplication across all studies
    # unique_titles = []
    # seen_normalized = set()

    # for title in all_reference_titles:
    #     normalized_title = _normalize_title(title)
    #     if normalized_title not in seen_normalized:
    #         unique_titles.append(title)
    #         seen_normalized.add(normalized_title)

    tasks = [
        _extract_references_from_study(
            study,
            extract_reference_titles_prompt,
            client,
            llm_name,
        )
        for study in valid_studies
    ]
    result = await asyncio.gather(*tasks)
    all_reference_titles = [x for sublist in result for x in sublist]

    unique_titles = []
    seen_normalized = set()

    for title in all_reference_titles:
        normalized_title = _normalize_title(title)
        if normalized_title not in seen_normalized:
            unique_titles.append(title)
            seen_normalized.add(normalized_title)

    # Convert to ResearchStudy objects
    reference_research_study_list = [
        ResearchStudy(title=title) for title in unique_titles
    ]

    logger.info(
        f"Total unique reference studies found: {len(reference_research_study_list)}"
    )
    return reference_research_study_list
