import asyncio
import json
import logging

from jinja2 import Environment

from airas.services.api_client.langchain_client import LangChainClient
from airas.services.api_client.llm_specs import OPENAI_MODELS

logger = logging.getLogger(__name__)

OPENAI_MODELS_SET = set(OPENAI_MODELS.__args__)


async def search_arxiv_id_from_title(
    llm_name: OPENAI_MODELS,
    llm_client: LangChainClient,
    prompt_template: str,
    paper_titles: list[str],
    conference_preference: str | None = None,
) -> list[str]:
    # TODO:Reflect the following judgment logic in llm_config.py.
    if llm_name not in OPENAI_MODELS_SET:
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
            output = await llm_client.generate(
                message=prompt, llm_name=llm_name, web_search=True
            )
        except Exception as e:
            logger.error(f"Web search failed for '{title}': {e}")
            return ""

        output_dict: dict | None = None
        for output_item in output:
            if output_item.get("text"):
                output_dict = json.loads(output_item.get("text"))
        if not output_dict:
            logger.warning(
                "No output received for '%s'. Appending empty result.", title
            )
            return ""

        arxiv_id = output_dict.get("arxiv_id", "").strip()
        if not arxiv_id:
            logger.warning("No arXiv ID found for '%s'.", title)
            return ""

        logger.info(f"Found arXiv ID for '{title}': {arxiv_id}")
        return arxiv_id

    logger.info(f"Processing {len(paper_titles)} paper titles")
    arxiv_id_list: list[str] = list(
        await asyncio.gather(*(_retrieve_arxiv_id(title) for title in paper_titles))
    )

    return arxiv_id_list
