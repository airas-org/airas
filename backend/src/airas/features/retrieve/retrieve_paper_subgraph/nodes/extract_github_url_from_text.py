import asyncio
import re
from logging import getLogger
from urllib.parse import urlparse

from jinja2 import Environment, Template
from pydantic import BaseModel

from airas.features.retrieve.retrieve_paper_subgraph.nodes.summarize_paper import (
    PaperSummary,
)
from airas.services.api_client.github_client import GithubClient
from airas.services.api_client.langchain_client import LangChainClient
from airas.services.api_client.llm_specs import LLM_MODELS

logger = getLogger(__name__)


class LLMOutput(BaseModel):
    index: int | None


def _extract_github_urls_from_text(
    paper_text: str, github_client: GithubClient
) -> list[str]:
    try:
        matches = re.findall(r"https?://github\.com/[\w\-\_]+/[\w\-\_]+", paper_text)
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
    paper_summary: PaperSummary | None,
    candidates: list[str],
    prompt_template: Template,
    llm_client: LangChainClient,
    llm_name: LLM_MODELS,
) -> str:
    messages = prompt_template.render(
        {
            "paper_summary": paper_summary,
            "extract_github_url_list": candidates,
        }
    )
    output, _ = await llm_client.structured_outputs(
        message=messages,
        data_model=LLMOutput,
        llm_name=llm_name,
    )

    if output is None:
        logger.warning("LLM returned no data when selecting GitHub URL")
        return ""

    if isinstance(output, BaseModel):
        idx = output.index
    else:
        idx = output.get("index") if isinstance(output, dict) else None

    if idx is None or not 0 <= idx < len(candidates):
        logger.warning("Failed to select a valid GitHub URL from candidates")
        return ""

    return candidates[idx]


async def extract_github_url_from_text(
    llm_name: LLM_MODELS,
    prompt_template: str,
    arxiv_full_text_list: list[list[str]],
    paper_summary_list: list[list[PaperSummary]],
    llm_client: LangChainClient,
    github_client: GithubClient,
) -> list[list[str]]:
    template = Environment().from_string(prompt_template)
    github_url_list: list[list[str]] = [
        ["" for _ in text_group] for text_group in arxiv_full_text_list
    ]

    async def _select_for_position(
        group_idx: int,
        paper_idx: int,
        summary: PaperSummary | None,
        candidates: list[str],
    ) -> tuple[int, int, str]:
        selected = await _select_github_url(
            paper_summary=summary,
            candidates=candidates,
            prompt_template=template,
            llm_client=llm_client,
            llm_name=llm_name,
        )
        return group_idx, paper_idx, selected

    selection_tasks = []

    for group_idx, text_group in enumerate(arxiv_full_text_list):
        summary_group = (
            paper_summary_list[group_idx] if group_idx < len(paper_summary_list) else []
        )
        for paper_idx, paper_text in enumerate(text_group):
            candidates = _extract_github_urls_from_text(paper_text, github_client)
            if not candidates:
                logger.info(
                    "No GitHub URLs found (group=%s, index=%s)", group_idx, paper_idx
                )
                continue

            paper_summary = (
                summary_group[paper_idx] if paper_idx < len(summary_group) else None
            )
            selection_tasks.append(
                _select_for_position(group_idx, paper_idx, paper_summary, candidates)
            )

    if selection_tasks:
        results = await asyncio.gather(*selection_tasks)
        for group_idx, paper_idx, selected_url in results:
            github_url_list[group_idx][paper_idx] = selected_url

    return github_url_list
