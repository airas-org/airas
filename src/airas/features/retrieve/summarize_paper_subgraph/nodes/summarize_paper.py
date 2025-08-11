import logging

from jinja2 import Environment
from pydantic import BaseModel

from airas.services.api_client.llm_client.llm_facade_client import (
    LLM_MODEL,
    LLMFacadeClient,
)
from airas.types.research_study import LLMExtractedInfo, ResearchStudy

logger = logging.getLogger(__name__)


class LLMOutput(BaseModel):
    main_contributions: str
    methodology: str
    experimental_setup: str
    limitations: str
    future_research_directions: str


def summarize_paper(
    llm_name: LLM_MODEL,
    prompt_template: str,
    research_study_list: list[ResearchStudy],
    client: LLMFacadeClient | None = None,
) -> list[ResearchStudy]:
    if client is None:
        client = LLMFacadeClient(llm_name=llm_name)

    env = Environment()
    template = env.from_string(prompt_template)

    for research_study in research_study_list:
        if not research_study.full_text:
            logger.warning(
                f"No full text available for '{research_study.title or 'N/A'}', skipping summarization."
            )
            continue

        data = {
            "paper_text": research_study.full_text,
        }
        messages = template.render(data)

        try:
            output, _ = client.structured_outputs(
                message=messages, data_model=LLMOutput
            )
            logger.info(f"Successfully summarized '{research_study.title or 'N/A'}'")
        except Exception as e:
            logger.error(f"Failed to summarize '{research_study.title or 'N/A'}': {e}")
            continue

        research_study.llm_extracted_info = LLMExtractedInfo(**output)

    return research_study_list
