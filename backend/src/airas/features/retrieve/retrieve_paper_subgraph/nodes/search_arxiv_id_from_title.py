import asyncio
import logging

from jinja2 import Environment

from airas.services.api_client.llm_client.llm_facade_client import LLMFacadeClient
from airas.services.api_client.llm_client.openai_client import OPENAI_MODEL

logger = logging.getLogger(__name__)

OPENAI_MODEL_SET = set(OPENAI_MODEL.__args__)


async def search_arxiv_id_from_title(
    llm_name: OPENAI_MODEL,
    llm_client: LLMFacadeClient,
    prompt_template: str,
    paper_titles: list[str],
    conference_preference: str | None = None,
) -> list[str]:
    # TODO:Reflect the following judgment logic in llm_config.py.
    if llm_name not in OPENAI_MODEL_SET:
        raise ValueError(
            f"It needs to be an OpenAI model. Invalid model name: {llm_name}"
        )
    template = Environment().from_string(prompt_template)

    async def _retrieve_arxiv_id(title: str) -> str:
        prompt = template.render(
            {
                "title": title,
                "conference_preference": conference_preference,
            }
        )
        try:
            output, _ = await llm_client.web_search(message=prompt, llm_name=llm_name)
        except Exception as e:
            logger.error(f"Web search failed for '{title}': {e}")
            return ""

        if not output or not isinstance(output, dict):
            logger.warning(f"No output received for '{title}'. Appending empty result.")
            return ""

        if not (arxiv_id := output.get("arxiv_id", "").strip()):
            logger.warning(f"No arXiv ID found for '{title}'.")
            return ""

        logger.info(f"Found arXiv ID for '{title}': {arxiv_id}")
        return arxiv_id

    logger.info(f"Processing {len(paper_titles)} paper titles")
    arxiv_id_list: list[str] = list(
        await asyncio.gather(*(_retrieve_arxiv_id(title) for title in paper_titles))
    )

    return arxiv_id_list
