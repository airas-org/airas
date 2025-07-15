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

logger = getLogger(__name__)


class LLMOutput(BaseModel):
    index: int | None


def _extract_github_urls_from_text(text: str, github_client: GithubClient) -> list[str]:
    try:
        matches = re.findall(r"https?://github\.com/[\w\-\_]+/[\w\-\_]+", text)
        valid_urls: list[str] = []
        for url in matches:
            url = url.replace("http://", "https://")
            if _is_valid_github_url(url, github_client):
                valid_urls.append(url)
        return valid_urls
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


def _select_github_url(
    paper_summary: str,
    candidates: list[str],
    prompt_template: str,
    llm_client: LLMFacadeClient,
) -> int | None:
    env = Environment()
    template = env.from_string(prompt_template)
    data = {
        "paper_summary": paper_summary,
        "extract_github_url_list": candidates,
    }
    prompt = template.render(data)

    try:
        output, cost = llm_client.structured_outputs(
            message=prompt, data_model=LLMOutput
        )
        if output is None:
            logger.warning("Error: No response from LLM.")
            return None
        return output["index"]
    except Exception as e:
        logger.warning(f"Error during LLM selection: {e}")
        return None


def extract_github_url_from_text(
    text: str,
    paper_summary: str,
    llm_name: LLM_MODEL,
    prompt_template: str,
    llm_client: LLMFacadeClient | None = None,
    github_client: GithubClient | None = None,
) -> str:
    if llm_client is None:
        llm_client = LLMFacadeClient(llm_name=llm_name)
    if github_client is None:
        github_client = GithubClient()

    candidates = _extract_github_urls_from_text(text, github_client)
    if not candidates:
        return ""

    idx = _select_github_url(paper_summary, candidates, prompt_template, llm_client)
    if idx is None or not (0 <= idx < len(candidates)):
        return ""
    return candidates[idx]
