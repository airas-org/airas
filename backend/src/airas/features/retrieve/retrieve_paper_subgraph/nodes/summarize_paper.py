import asyncio
import logging
from typing import Any, Self, cast

from jinja2 import Environment, Template
from pydantic import BaseModel

from airas.services.api_client.langchain_client import LangChainClient
from airas.services.api_client.llm_specs import LLM_MODELS

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
    llm_name: LLM_MODELS,
    group_idx: int,
    paper_idx: int,
) -> tuple[int, int, PaperSummary]:
    messages = rendered_template.render(
        {
            "paper_text": paper_text,
        }
    )

    try:
        output, _ = await llm_client.structured_outputs(
            message=messages,
            data_model=PaperSummary,
            llm_name=llm_name,
        )
        if output is None:
            logger.error(
                "LLM returned no data (group=%s, index=%s)",
                group_idx,
                paper_idx,
            )
            return group_idx, paper_idx, PaperSummary.empty()
        logger.info(
            "Successfully summarized paper (group=%s, index=%s)",
            group_idx,
            paper_idx,
        )
        return (
            group_idx,
            paper_idx,
            (
                output
                if isinstance(output, PaperSummary)
                else PaperSummary(**cast(dict[str, Any], output))
            ),
        )

    except Exception as e:
        logger.error(
            "Failed to summarize paper (group=%s, index=%s): %s",
            group_idx,
            paper_idx,
            e,
        )
        return group_idx, paper_idx, PaperSummary.empty()


async def summarize_paper(
    llm_name: LLM_MODELS,
    llm_client: LangChainClient,
    prompt_template: str,
    arxiv_full_text_list: list[list[str]],
) -> list[list[PaperSummary]]:
    env = Environment()
    template = env.from_string(prompt_template)

    summaries: list[list[PaperSummary]] = [
        [PaperSummary.empty() for _ in text_group]
        for text_group in arxiv_full_text_list
    ]

    tasks = [
        _summarize_single_text(
            paper_text=paper_text,
            rendered_template=template,
            llm_client=llm_client,
            llm_name=llm_name,
            group_idx=group_idx,
            paper_idx=paper_idx,
        )
        for group_idx, text_group in enumerate(arxiv_full_text_list)
        for paper_idx, paper_text in enumerate(text_group)
        if paper_text.strip()
    ]

    if not tasks:
        return summaries

    results = await asyncio.gather(*tasks)
    for group_idx, paper_idx, llm_output in results:
        summaries[group_idx][paper_idx] = llm_output

    return summaries
