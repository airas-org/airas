import asyncio
import logging
from typing import TypeVar, cast

from jinja2 import Environment
from pydantic import BaseModel

from airas.features.retrieve.retrieve_paper_subgraph.nodes.summarize_paper import (
    PaperSummary,
)
from airas.features.retrieve.retrieve_paper_subgraph.prompt.extract_experimental_info_prompt import (
    extract_experimental_info_prompt,
)
from airas.services.api_client.langchain_client import LangChainClient
from airas.services.api_client.llm_specs import LLM_MODELS

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
        output, _ = await llm_client.structured_outputs(
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
    paper_summary_list: list[list[PaperSummary]],
    github_code_list: list[list[str]],
    prompt_template: str = extract_experimental_info_prompt,
    max_workers: int = 3,
) -> tuple[list[list[str]], list[list[str]]]:
    if len(paper_summary_list) != len(github_code_list):
        raise ValueError(
            "paper_summary_list and github_code_list must contain the same number of query groups before extracting experimental info."
        )
    for idx, (study_group, code_group) in enumerate(
        zip(paper_summary_list, github_code_list, strict=True)
    ):
        if len(study_group) != len(code_group):
            raise ValueError(
                f"paper_summary_list[{idx}] and github_code_list[{idx}] must contain the same number of items before extracting experimental info."
            )

    experimental_info_list: list[list[str]] = [
        ["" for _ in group] for group in paper_summary_list
    ]
    experimental_code_list: list[list[str]] = [
        ["" for _ in group] for group in paper_summary_list
    ]
    semaphore = asyncio.Semaphore(max(1, max_workers))

    async def _run_task(
        group_idx: int,
        study_idx: int,
        paper_summary: PaperSummary,
        code_str: str,
    ) -> None:
        async with semaphore:
            (
                experimental_info,
                experimental_code,
            ) = await _extract_experimental_info_from_study(
                paper_summary,
                code_str,
                prompt_template,
                llm_client,
                llm_name,
            )
            experimental_info_list[group_idx][study_idx] = experimental_info
            experimental_code_list[group_idx][study_idx] = experimental_code

    tasks: list[asyncio.Task[None]] = []
    for group_idx, (study_group, code_group) in enumerate(
        zip(paper_summary_list, github_code_list, strict=True)
    ):
        for study_idx, (arxiv_summary, code_str) in enumerate(
            zip(study_group, code_group, strict=True)
        ):
            tasks.append(
                asyncio.create_task(
                    _run_task(group_idx, study_idx, arxiv_summary, code_str)
                )
            )

    if tasks:
        await asyncio.gather(*tasks)

    return experimental_info_list, experimental_code_list
