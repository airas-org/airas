import asyncio
import logging

from jinja2 import Environment
from pydantic import BaseModel

from airas.features.retrieve.retrieve_code_subgraph.prompt.extract_experimental_info_prompt import (
    extract_experimental_info_prompt,
)
from airas.services.api_client.llm_client.llm_facade_client import (
    LLM_MODEL,
    LLMFacadeClient,
)
from airas.types.github import GitHubRepositoryInfo
from airas.types.research_study import ResearchStudy

logger = logging.getLogger(__name__)


class LLMOutput(BaseModel):
    experimental_code: str
    experimental_info: str


async def _extract_experimental_info_from_study(
    research_study: ResearchStudy,
    code_str: str,
    template: str,
    client: LLMFacadeClient,
    github_repository_info: GitHubRepositoryInfo,
    llm_name: LLM_MODEL,
    index: int,
) -> None:
    title = research_study.title or "N/A"

    if not code_str:
        logger.info(
            f"No code available for '{title}', skipping experimental info extraction."
        )
        return

    if not (
        research_study.llm_extracted_info
        and research_study.llm_extracted_info.methodology
    ):
        logger.warning(
            f"No llm_extracted_info or no methodology available for '{title}', skipping experimental info extraction."
        )
        return

    env = Environment()
    jinja_template = env.from_string(template)
    messages = jinja_template.render(
        {
            "method_text": research_study.llm_extracted_info.methodology,
            "repository_content_str": code_str,
        }
    )

    try:
        output, _ = await client.structured_outputs_async(
            message=messages, data_model=LLMOutput
        )
    except Exception as e:
        logger.error(f"Error extracting experimental info for '{title}': {e}")
        return

    if not output or not isinstance(output, dict):
        logger.error(f"No response from LLM for '{title}'")
        return
    research_study.llm_extracted_info.experimental_code = output["experimental_code"]
    research_study.llm_extracted_info.experimental_info = output["experimental_info"]
    logger.info(f"Successfully extracted experimental info for '{title}'")

    return


async def extract_experimental_info(
    llm_name: LLM_MODEL,
    research_study_list: list[ResearchStudy],
    code_str_list: list[str],
    github_repository_info: GitHubRepositoryInfo,
    prompt_template: str = extract_experimental_info_prompt,
    client: LLMFacadeClient | None = None,
    max_workers: int = 3,
) -> list[ResearchStudy]:
    client = client or LLMFacadeClient(llm_name=llm_name)

    if len(research_study_list) != len(code_str_list):
        raise ValueError(
            "research_study_list and code_str_list must have the same length"
        )

    logger.info(
        f"Processing {len(research_study_list)} studies with {max_workers} workers"
    )
    tasks = [
        _extract_experimental_info_from_study(
            research_study,
            code_str,
            prompt_template,
            client,
            github_repository_info,
            llm_name,
            index,
        )
        for index, (research_study, code_str) in enumerate(
            zip(research_study_list, code_str_list, strict=True)
        )
    ]
    await asyncio.gather(*tasks)
    return research_study_list
