import asyncio
import re
from logging import getLogger
from urllib.parse import urlparse

from jinja2 import Environment
from pydantic import BaseModel

from airas.services.api_client.github_client import GithubClient
from airas.services.api_client.llm_client.llm_facade_client import (
    LLM_MODEL,
    LLMFacadeClient,
)
from airas.types.github import GitHubRepositoryInfo
from airas.types.research_study import MetaData, ResearchStudy

logger = getLogger(__name__)


class LLMOutput(BaseModel):
    index: int | None


def _extract_github_urls_from_text(
    paper_full_text: str, github_client: GithubClient
) -> list[str]:
    try:
        matches = re.findall(
            r"https?://github\.com/[\w\-\_]+/[\w\-\_]+", paper_full_text
        )
        return [
            url.replace("http://", "https://")
            for url in matches
            if _is_valid_github_url(url.replace("http://", "https://"), github_client)
        ]
    except Exception as e:
        logger.warning(f"Error extracting GitHub URL: {e}")
        return []


def _is_valid_github_url(github_url: str, github_client: GithubClient) -> bool:
    path = urlparse(github_url).path.strip("/")
    parts = path.split("/")
    if len(parts) < 2:
        return False
    github_owner, repository_name = parts[0], parts[1]

    try:
        info = github_client.get_repository(github_owner, repository_name)
        return info is not None
    except Exception:
        return False


async def _select_github_url(
    research_study: ResearchStudy,
    candidates: list[str],
    prompt_template: str,
    github_repository_info: GitHubRepositoryInfo,
    llm_client: LLMFacadeClient,
    llm_name: LLM_MODEL,
    index: int,
) -> None:
    paper_summary = research_study.llm_extracted_info.methodology
    template = Environment().from_string(prompt_template)
    messages = template.render(
        {"paper_summary": paper_summary, "extract_github_url_list": candidates}
    )
    output, _ = await llm_client.structured_outputs_async(
        message=messages, data_model=LLMOutput
    )
    if output is None:
        logger.warning("Error during LLM selection")
        return None
    idx = output["index"] if output else None

    if idx is not None and 0 <= idx < len(candidates):
        if not research_study.meta_data:
            research_study.meta_data = MetaData()
        research_study.meta_data.github_url = candidates[idx]
        logger.info(
            f"Selected GitHub URL for '{research_study.title}': {candidates[idx]}"
        )
    else:
        logger.warning(
            f"Failed to select valid GitHub URL for '{research_study.title}'"
        )


async def extract_github_url_from_text(
    llm_name: LLM_MODEL,
    prompt_template: str,
    research_study_list: list[ResearchStudy],
    github_repository_info: GitHubRepositoryInfo | None = None,
    llm_client: LLMFacadeClient | None = None,
    github_client: GithubClient | None = None,
) -> list[ResearchStudy]:
    llm_client = llm_client or LLMFacadeClient(llm_name=llm_name)
    github_client = github_client or GithubClient()

    candidates_list: list[list[str]] = []
    for research_study in research_study_list:
        title = research_study.title or "N/A"

        if not research_study.full_text or not (
            research_study.llm_extracted_info
            and research_study.llm_extracted_info.methodology
        ):
            logger.warning(
                f"Missing full text or methodology for '{title}', skipping GitHub URL extraction."
            )
            candidates_list.append([])
            continue

        candidates = _extract_github_urls_from_text(
            research_study.full_text, github_client
        )
        if not candidates:
            logger.info(f"No GitHub URLs found for '{title}'")
            candidates_list.append([])
            continue
        candidates_list.append(candidates)

    tasks = [
        _select_github_url(
            research_study,
            candidates,
            prompt_template,
            github_repository_info,
            llm_client,
            llm_name,
            index,
        )
        for index, (research_study, candidates) in enumerate(
            zip(research_study_list, candidates_list, strict=True)
        )
    ]

    await asyncio.gather(*tasks)

    return research_study_list
