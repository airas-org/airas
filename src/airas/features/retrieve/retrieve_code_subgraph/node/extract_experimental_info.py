import logging
from concurrent.futures import ThreadPoolExecutor, as_completed

from jinja2 import Environment
from pydantic import BaseModel

from airas.features.retrieve.retrieve_code_subgraph.prompt.extract_experimental_info_prompt import (
    extract_experimental_info_prompt,
)
from airas.services.api_client.llm_client.llm_facade_client import (
    LLM_MODEL,
    LLMFacadeClient,
)
from airas.types.research_study import ResearchStudy

logger = logging.getLogger(__name__)


class LLMOutput(BaseModel):
    experimental_code: str
    experimental_info: str


def _extract_experimental_info_from_study(
    research_study: ResearchStudy,
    code_str: str,
    template: str,
    client: LLMFacadeClient,
) -> ResearchStudy:
    title = research_study.title or "N/A"

    if not code_str:
        logger.info(
            f"No code available for '{title}', skipping experimental info extraction."
        )
        return research_study

    if not (
        research_study.llm_extracted_info
        and research_study.llm_extracted_info.methodology
    ):
        logger.warning(
            f"No llm_extracted_info or no methodology available for '{title}', skipping experimental info extraction."
        )
        return research_study

    env = Environment()
    jinja_template = env.from_string(template)
    messages = jinja_template.render(
        {
            "method_text": research_study.llm_extracted_info.methodology,
            "repository_content_str": code_str,
        }
    )

    try:
        output, _ = client.structured_outputs(message=messages, data_model=LLMOutput)
    except Exception as e:
        logger.error(f"Error extracting experimental info for '{title}': {e}")
        return research_study

    if not output or not isinstance(output, dict):
        logger.error(f"No response from LLM for '{title}'")
        return research_study

    research_study.llm_extracted_info.experimental_code = output["experimental_code"]
    research_study.llm_extracted_info.experimental_info = output["experimental_info"]
    logger.info(f"Successfully extracted experimental info for '{title}'")

    return research_study


def extract_experimental_info(
    llm_name: LLM_MODEL,
    research_study_list: list[ResearchStudy],
    code_str_list: list[str],
    prompt_template: str = extract_experimental_info_prompt,
    client: LLMFacadeClient | None = None,
    max_workers: int = 3,
) -> list[ResearchStudy]:
    client = client or LLMFacadeClient(llm_name=llm_name)

    if len(research_study_list) != len(code_str_list):
        raise ValueError(
            "research_study_list and code_str_list must have the same length"
        )

    logger.info(
        f"Processing {len(research_study_list)} studies with {max_workers} workers"
    )

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_index = {
            executor.submit(
                _extract_experimental_info_from_study,
                study,
                code_str,
                prompt_template,
                client,
            ): i
            for i, (study, code_str) in enumerate(
                zip(research_study_list, code_str_list)  # noqa: B905
            )
        }

        # Results will be stored in order
        results = [None] * len(research_study_list)
        for future in as_completed(future_to_index):
            index = future_to_index[future]
            try:
                updated_study = future.result()
                results[index] = updated_study
            except Exception as e:
                study = research_study_list[index]
                title = study.title or "N/A"
                logger.error(f"Error processing study '{title}': {e}")
                results[index] = study  # Return original study if processing fails

    # Filter out None values (shouldn't happen with current logic)
    updated_studies = [study for study in results if study is not None]

    logger.info(f"Completed processing {len(updated_studies)} studies")
    return updated_studies
