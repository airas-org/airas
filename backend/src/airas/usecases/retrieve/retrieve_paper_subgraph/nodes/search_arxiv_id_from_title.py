import asyncio
import logging

from jinja2 import Environment
from pydantic import BaseModel

from airas.core.llm_config import NodeLLMConfig
from airas.infra.langchain_client import LangChainClient

logger = logging.getLogger(__name__)


class ArxivIdOutput(BaseModel):
    arxiv_id: str


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
            output = await llm_client.structured_outputs(
                llm_name=llm_config.llm_name,
                message=prompt,
                data_model=ArxivIdOutput,
                params=llm_config.params,
                web_search=True,
            )

            if output is None:
                logger.warning(f"No output received for '{title}'")
                return ""

            if isinstance(output, ArxivIdOutput):
                arxiv_id = output.arxiv_id
            elif isinstance(output, dict):
                arxiv_id = output.get("arxiv_id", "")
            else:
                logger.warning(f"Unexpected output type for '{title}': {type(output)}")
                return ""

            arxiv_id = arxiv_id.strip()
            if not arxiv_id:
                logger.warning(f"No arXiv ID found for '{title}'.")
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
