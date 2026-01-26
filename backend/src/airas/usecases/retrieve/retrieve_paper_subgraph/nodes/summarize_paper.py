import asyncio
import logging
from typing import Any, Self, cast

from jinja2 import Environment, Template
from pydantic import BaseModel

from airas.core.llm_config import NodeLLMConfig
from airas.infra.langchain_client import LangChainClient

logger = logging.getLogger(__name__)

DEFAULT_FIELD_VALUE = "[Unavailable]"


class PaperSummary(BaseModel):
    main_contributions: str = DEFAULT_FIELD_VALUE
    methodology: str = DEFAULT_FIELD_VALUE
    experimental_setup: str = DEFAULT_FIELD_VALUE
    limitations: str = DEFAULT_FIELD_VALUE
    future_research_directions: str = DEFAULT_FIELD_VALUE

    @classmethod
    def empty(cls) -> Self:
        return cls()


async def _summarize_single_text(
    paper_text: str,
    rendered_template: Template,
    llm_client: LangChainClient,
    llm_config: NodeLLMConfig,
    paper_idx: int,
) -> PaperSummary:
    messages = rendered_template.render(
        {
            "paper_text": paper_text,
        }
    )

    try:
        output = await llm_client.structured_outputs(
            message=messages,
            data_model=PaperSummary,
            llm_name=llm_config.llm_name,
            params=llm_config.params,
        )
        if output is None:
            logger.error("LLM returned no data (index=%s)", paper_idx)
            return PaperSummary.empty()
        logger.info("Successfully summarized paper (index=%s)", paper_idx)
        return (
            output
            if isinstance(output, PaperSummary)
            else PaperSummary(**cast(dict[str, Any], output))
        )

    except Exception as e:
        logger.error("Failed to summarize paper (index=%s): %s", paper_idx, e)
        return PaperSummary.empty()


async def summarize_paper(
    llm_config: NodeLLMConfig,
    llm_client: LangChainClient,
    prompt_template: str,
    arxiv_full_text_list: list[str],
) -> list[PaperSummary]:
    env = Environment()
    template = env.from_string(prompt_template)

    async def _summarize_or_empty(idx: int, text: str) -> PaperSummary:
        if not text.strip():
            return PaperSummary.empty()
        return await _summarize_single_text(
            paper_text=text,
            rendered_template=template,
            llm_client=llm_client,
            llm_config=llm_config,
            paper_idx=idx,
        )

    summaries: list[PaperSummary] = list(
        await asyncio.gather(
            *(
                _summarize_or_empty(idx, text)
                for idx, text in enumerate(arxiv_full_text_list)
            )
        )
    )

    return summaries
