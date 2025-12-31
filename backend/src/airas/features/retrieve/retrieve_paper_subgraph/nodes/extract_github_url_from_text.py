import asyncio
import re
from logging import getLogger
from urllib.parse import urlparse

from jinja2 import Environment, Template
from pydantic import BaseModel, field_validator

from airas.features.retrieve.retrieve_paper_subgraph.nodes.summarize_paper import (
    PaperSummary,
)
from airas.services.api_client.github_client import GithubClient
from airas.services.api_client.langchain_client import LangChainClient
from airas.services.api_client.llm_specs import LLM_MODELS

logger = getLogger(__name__)


class LLMOutput(BaseModel):
    index: int | None

    @field_validator("index", mode="before")
    @classmethod
    def parse_index(cls, v):
        if isinstance(v, str):
            if v.lower() in ("none", "null", ""):
                return None

            try:
                return int(v)
            except ValueError:
                logger.warning(f"Could not parse index value: {v}")
                return None
        return v


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

    if isinstance(output, LLMOutput):
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
    arxiv_full_text_list: list[str],
    paper_summary_list: list[PaperSummary],
    llm_client: LangChainClient,
    github_client: GithubClient,
) -> list[str]:
    template = Environment().from_string(prompt_template)

    async def _extract_for_paper(
        paper_idx: int,
        paper_text: str,
        summary: PaperSummary | None,
    ) -> str:
        if not (
            candidates := _extract_github_urls_from_text(paper_text, github_client)
        ):
            logger.info(f"No GitHub URLs found (index={paper_idx})")
            return ""

        return await _select_github_url(
            paper_summary=summary,
            candidates=candidates,
            prompt_template=template,
            llm_client=llm_client,
            llm_name=llm_name,
        )

    github_url_list: list[str] = list(
        await asyncio.gather(
            *(
                _extract_for_paper(
                    paper_idx=idx,
                    paper_text=text,
                    summary=paper_summary_list[idx]
                    if idx < len(paper_summary_list)
                    else None,
                )
                for idx, text in enumerate(arxiv_full_text_list)
            )
        )
    )

    return github_url_list
