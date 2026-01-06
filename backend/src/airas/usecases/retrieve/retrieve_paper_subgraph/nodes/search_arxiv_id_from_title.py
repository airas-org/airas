import asyncio
import json
import logging
from typing import get_args

from jinja2 import Environment

from airas.core.llm_config import NodeLLMConfig
from airas.infra.langchain_client import LangChainClient
from airas.infra.llm_specs import OPENAI_MODELS

logger = logging.getLogger(__name__)

OPENAI_MODELS_SET = set(get_args(OPENAI_MODELS))


async def search_arxiv_id_from_title(
    llm_config: NodeLLMConfig,
    llm_client: LangChainClient,
    prompt_template: str,
    paper_titles: list[str],
    conference_preference: str | None = None,
) -> list[str]:
    # TODO: Reflect the following judgment logic in llm_config.py.
    if llm_config.llm_name not in OPENAI_MODELS_SET:
        raise ValueError(
            f"It needs to be an OpenAI model. Invalid model name: {llm_config.llm_name}"
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
                message=prompt, llm_name=llm_config.llm_name, web_search=True
            )
            output_dict = json.loads(output)
        except json.JSONDecodeError as e:
            logger.warning(f"Failed to parse JSON output for '{title}': {e}")
            return ""
        except Exception as e:
            logger.error(f"Web search failed for '{title}': {e}")
            return ""

        if not output_dict:
            logger.warning(f"No output received for '{title}'. Appending empty result.")
            return ""

        if not (arxiv_id := output_dict.get("arxiv_id", "").strip()):
            logger.warning(f"No arXiv ID found for '{title}'.")
            return ""

        logger.info(f"Found arXiv ID for '{title}': {arxiv_id}")
        return arxiv_id

    logger.info(f"Processing {len(paper_titles)} paper titles")
    arxiv_id_list: list[str] = list(
        await asyncio.gather(*(_retrieve_arxiv_id(title) for title in paper_titles))
    )

    return arxiv_id_list
