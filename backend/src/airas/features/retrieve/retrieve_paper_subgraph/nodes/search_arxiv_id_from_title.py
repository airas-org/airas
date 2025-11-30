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
    retrieve_paper_title_list: list[list[str]],
    conference_preference: str | None = None,
) -> list[list[str]]:
    # TODO:Reflect the following judgment logic in llm_config.py.
    if llm_name not in OPENAI_MODEL_SET:
        raise ValueError(
            f"It needs to be an OpenAI model. Invalid model name: {llm_name}"
        )
    template = Environment().from_string(prompt_template)

    arxiv_id_list: list[list[str]] = []

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
            logger.error(
                "Web search failed for '%s': %s. Appending empty result.",
                title,
                e,
            )
            return ""

        if not output or not isinstance(output, dict):
            logger.warning(
                "No output received for '%s'. Appending empty result.", title
            )
            return ""

        arxiv_id = output.get("arxiv_id", "").strip()
        if not arxiv_id:
            logger.warning("No arXiv ID found for '%s'.", title)
            return ""

        logger.info("Found arXiv ID for '%s': %s", title, arxiv_id)
        return arxiv_id

    for idx, title_group in enumerate(retrieve_paper_title_list):
        logger.info(
            "Processing title group %d/%d", idx + 1, len(retrieve_paper_title_list)
        )
        # issue LLM web searches concurrently to hide API latency per group
        group_results: list[str] = list(
            await asyncio.gather(*(_retrieve_arxiv_id(title) for title in title_group))
        )

        arxiv_id_list.append(group_results)

    return arxiv_id_list
