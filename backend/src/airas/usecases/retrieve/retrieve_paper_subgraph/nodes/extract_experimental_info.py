import asyncio
import logging
from typing import TypeVar, cast

from jinja2 import Environment
from pydantic import BaseModel

from airas.infra.langchain_client import LangChainClient
from airas.infra.llm_specs import LLM_MODELS
from airas.usecases.retrieve.retrieve_paper_subgraph.nodes.summarize_paper import (
    PaperSummary,
)
from airas.usecases.retrieve.retrieve_paper_subgraph.prompt.extract_experimental_info_prompt import (
    extract_experimental_info_prompt,
)

T = TypeVar("T")

logger = logging.getLogger(__name__)


class LLMOutput(BaseModel):
    experimental_code: str
    experimental_info: str


async def _extract_experimental_info_from_study(
    paper_summary: PaperSummary,
    code_str: str,
    template: str,
    llm_client: LangChainClient,
    llm_name: LLM_MODELS,
) -> tuple[str, str]:
    env = Environment()
    jinja_template = env.from_string(template)
    messages = jinja_template.render(
        {
            "paper_summary": paper_summary,
            "repository_content_str": code_str,
        }
    )

    try:
        output = await llm_client.structured_outputs(
            message=messages,
            data_model=LLMOutput,
            llm_name=llm_name,
        )
    except Exception as e:
        logger.error(f"Error extracting experimental info for study: {e}")
        return "", ""

    llm_output = cast(LLMOutput, output)

    return llm_output.experimental_info, llm_output.experimental_code


async def extract_experimental_info(
    llm_name: LLM_MODELS,
    llm_client: LangChainClient,
    paper_summary_list: list[PaperSummary],
    github_code_list: list[str],
    prompt_template: str = extract_experimental_info_prompt,
    max_workers: int = 3,
) -> tuple[list[str], list[str]]:
    if len(paper_summary_list) != len(github_code_list):
        raise ValueError(
            "paper_summary_list and github_code_list must have the same length."
        )

    semaphore = asyncio.Semaphore(max(1, max_workers))

    async def _run_task(
        paper_summary: PaperSummary,
        code_str: str,
    ) -> tuple[str, str]:
        async with semaphore:
            return await _extract_experimental_info_from_study(
                paper_summary,
                code_str,
                prompt_template,
                llm_client,
                llm_name,
            )

    results = await asyncio.gather(
        *(
            _run_task(summary, code)
            for summary, code in zip(paper_summary_list, github_code_list, strict=True)
        )
    )

    experimental_info_list = [info for info, _ in results]
    experimental_code_list = [code for _, code in results]

    return experimental_info_list, experimental_code_list
