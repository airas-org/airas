import logging

from jinja2 import Environment

from airas.services.api_client.llm_client.llm_facade_client import (
    LLMFacadeClient,
)
from airas.services.api_client.llm_client.openai_client import OPENAI_MODEL
from airas.types.research_study import MetaData, ResearchStudy

logger = logging.getLogger(__name__)

OPENAI_MODEL_SET = set(OPENAI_MODEL.__args__)


async def search_arxiv_id_from_title(
    llm_name: OPENAI_MODEL,
    llm_client: LLMFacadeClient,
    prompt_template: str,
    research_study_list: list[ResearchStudy],
    conference_preference: str | None = None,
) -> list[ResearchStudy]:
    # TODO:Reflect the following judgment logic in llm_config.py.
    if llm_name not in OPENAI_MODEL_SET:
        raise ValueError(
            f"It needs to be an OpenAI model. Invalid model name: {llm_name}"
        )
    template = Environment().from_string(prompt_template)

    for idx, research_study in enumerate(research_study_list):
        logger.info(
            "Processing research study %d/%d", idx + 1, len(research_study_list)
        )
        prompt = template.render(
            {
                "title": research_study.title,
                "conference_preference": conference_preference,
            }
        )
        try:
            output, _ = await llm_client.web_search(message=prompt, llm_name=llm_name)
        except Exception as e:
            logger.error(
                f"Web search failed for '{research_study.title}': {e}. Skipping to the next."
            )
            continue

        if not output or not isinstance(output, dict):
            logger.warning(
                f"No output received for '{research_study.title}'. Skipping."
            )
            continue

        arxiv_id = output.get("arxiv_id", "").strip()
        if not arxiv_id:
            logger.warning(f"No arXiv ID found for '{research_study.title}'.")
            continue

        if not research_study.meta_data:
            research_study.meta_data = MetaData()
        research_study.meta_data.arxiv_id = arxiv_id
        logger.info(f"Found arXiv ID for '{research_study.title}': {arxiv_id}")

    return research_study_list
