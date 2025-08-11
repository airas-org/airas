import logging

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
    extract_code: str
    extract_info: str


def extract_experimental_info(
    llm_name: LLM_MODEL,
    research_study_list: list[ResearchStudy],
    code_str_list: list[str],
    prompt_template: str = extract_experimental_info_prompt,
    client: LLMFacadeClient | None = None,
) -> list[ResearchStudy]:
    client = client or LLMFacadeClient(llm_name=llm_name)
    template = Environment().from_string(prompt_template)

    for code_str, research_study in zip(
        code_str_list, research_study_list, strict=True
    ):
        title = research_study.title or "N/A"

        if not code_str:
            research_study.experimental_code = ""
            if research_study.llm_extracted_info:
                research_study.llm_extracted_info.experimental_info = ""
            logger.info(
                f"No code available for '{title}', skipping experimental info extraction."
            )
            continue

        if not (
            research_study.llm_extracted_info
            and research_study.llm_extracted_info.methodology
        ):
            logger.warning(
                f"No methodology available for '{title}', skipping experimental info extraction."
            )
            continue

        try:
            messages = template.render(
                {
                    "method_text": research_study.llm_extracted_info.methodology,
                    "repository_content_str": code_str,
                }
            )
            output, _ = client.structured_outputs(
                message=messages, data_model=LLMOutput
            )

            if output:
                research_study.llm_extracted_info.extracted_code = output[
                    "extract_code"
                ]
                research_study.llm_extracted_info.experimental_info = output[
                    "extract_info"
                ]
                logger.info(f"Successfully extracted experimental info for '{title}'")
            else:
                logger.error(f"No response from LLM for '{title}'")
        except Exception as e:
            logger.error(f"Error extracting experimental info for '{title}': {e}")

    return research_study_list
