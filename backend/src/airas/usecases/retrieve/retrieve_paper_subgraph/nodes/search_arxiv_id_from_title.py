import asyncio
import json
import logging
import re

from jinja2 import Environment

from airas.core.llm_config import NodeLLMConfig
from airas.infra.langchain_client import LangChainClient

logger = logging.getLogger(__name__)


def _extract_json_from_response(response: str) -> dict:
    code_block_match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", response, re.DOTALL)
    if code_block_match:
        try:
            return json.loads(code_block_match.group(1))
        except json.JSONDecodeError:
            pass

    json_match = re.search(r"\{[^{}]*\"arxiv_id\"[^{}]*\}", response)
    if json_match:
        try:
            return json.loads(json_match.group(0))
        except json.JSONDecodeError:
            pass

    return {}


async def search_arxiv_id_from_title(
    llm_config: NodeLLMConfig,
    llm_client: LangChainClient,
    prompt_template: str,
    paper_titles: list[str],
    conference_preference: str | None = None,
) -> list[str]:
    template = Environment().from_string(prompt_template)

    async def _retrieve_arxiv_id(title: str) -> str:
        prompt = template.render(
            {
                "title": title,
                "conference_preference": conference_preference,
            }
        )
        try:
            response = await llm_client.generate(
                llm_name=llm_config.llm_name,
                message=prompt,
                params=llm_config.params,
                web_search=True,
            )

            if not response:
                logger.warning(f"No response received for '{title}'")
                return ""

            output = _extract_json_from_response(response)
            arxiv_id = output.get("arxiv_id", "").strip()

            if not arxiv_id:
                logger.warning(f"No arXiv ID found for '{title}'")
                return ""

            logger.info(f"Found arXiv ID for '{title}': {arxiv_id}")
            return arxiv_id

        except Exception as e:
            logger.error(f"Web search failed for '{title}': {e}")
            return ""

    logger.info(f"Processing {len(paper_titles)} paper titles")
    arxiv_id_list: list[str] = list(
        await asyncio.gather(*(_retrieve_arxiv_id(title) for title in paper_titles))
    )

    return arxiv_id_list
