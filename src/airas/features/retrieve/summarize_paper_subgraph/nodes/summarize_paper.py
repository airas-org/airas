import asyncio
import json
import logging

from jinja2 import Environment, Template
from pydantic import BaseModel

from airas.services.api_client.llm_client.llm_facade_client import (
    LLM_MODEL,
    LLMFacadeClient,
)
from airas.types.github import GitHubRepositoryInfo
from airas.types.research_study import LLMExtractedInfo, ResearchStudy
from airas.utils.save_prompt import save_io_on_github

logger = logging.getLogger(__name__)


class LLMOutput(BaseModel):
    main_contributions: str
    methodology: str
    experimental_setup: str
    limitations: str
    future_research_directions: str


async def _summarize_single_study(
    index: int,
    research_study: ResearchStudy,
    rendered_template: Template,
    llm_name: LLM_MODEL,
    github_repository_info: GitHubRepositoryInfo,
    client: LLMFacadeClient,
) -> None:
    if not research_study.full_text:
        logger.warning(
            f"No full text available for '{research_study.title or 'N/A'}', skipping summarization."
        )
        return

    data = {
        "paper_text": research_study.full_text,
    }
    messages = rendered_template.render(data)

    try:
        output, _ = await client.structured_outputs_async(
            message=messages,
            data_model=LLMOutput,
        )
        logger.info(f"Successfully summarized '{research_study.title or 'N/A'}'")
    except Exception as e:
        logger.error(f"Failed to summarize '{research_study.title or 'N/A'}': {e}")
        return

    await asyncio.to_thread(
        save_io_on_github,
        github_repository_info,
        messages,
        json.dumps(output, ensure_ascii=False, indent=4),
        "summarize_paper_subgraph",
        f"summarize_paper_{index}",
        llm_name,
    )

    # 生成結果を study に反映
    research_study.llm_extracted_info = LLMExtractedInfo(**output)


async def summarize_paper(
    llm_name: LLM_MODEL,
    prompt_template: str,
    research_study_list: list[ResearchStudy],
    github_repository_info: GitHubRepositoryInfo,
    client: LLMFacadeClient | None = None,
) -> list[ResearchStudy]:
    if client is None:
        client = LLMFacadeClient(llm_name=llm_name)

    env = Environment()
    template = env.from_string(prompt_template)

    tasks = [
        _summarize_single_study(
            index,
            research_study,
            template,
            llm_name,
            github_repository_info,
            client,
        )
        for index, research_study in enumerate(research_study_list)
    ]

    await asyncio.gather(*tasks)

    return research_study_list
