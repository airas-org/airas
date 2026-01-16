import asyncio
import string
from logging import getLogger

from jinja2 import Environment
from pydantic import BaseModel

from airas.core.llm_config import NodeLLMConfig
from airas.infra.langchain_client import LangChainClient
from airas.usecases.retrieve.retrieve_paper_subgraph.prompt.extract_reference_titles_prompt import (
    extract_reference_titles_prompt,
)

logger = getLogger(__name__)


class LLMOutput(BaseModel):
    reference_titles: list[str]


# Possible to extract from different parts of the paper
def _normalize_title(title: str) -> str:
    normalized = title.lower()
    translator = str.maketrans("", "", string.punctuation)
    normalized = normalized.translate(translator)
    normalized = "".join(normalized.split())

    return normalized


async def _extract_references_from_text(
    full_text: str,
    template: str,
    llm_client: LangChainClient,
    llm_config: NodeLLMConfig,
    context_label: str,
) -> list[str]:
    if not full_text.strip():
        logger.warning(f"No full_text found for {context_label}")
        return []

    env = Environment()
    jinja_template = env.from_string(template)
    data = {"full_text": full_text}
    messages = jinja_template.render(data)

    try:
        output = await llm_client.structured_outputs(
            message=messages,
            data_model=LLMOutput,
            llm_name=llm_config.llm_name,
            params=llm_config.params,
        )
    except Exception as e:
        logger.error(f"Error extracting references for {context_label}: {e}")
        return []

    if output is None or not isinstance(output, LLMOutput):
        logger.warning(
            "Warning: No valid response from LLM for reference extraction for "
            f"{context_label}."
        )
        return []
    reference_titles = output.reference_titles
    logger.info(f"Found {len(reference_titles)} reference titles for {context_label}.")

    return reference_titles


def _deduplicate_titles(reference_titles: list[str]) -> list[str]:
    unique_titles: list[str] = []
    seen_normalized: set[str] = set()
    for title in reference_titles:
        normalized_title = _normalize_title(title)
        if not normalized_title or normalized_title in seen_normalized:
            continue
        unique_titles.append(title)
        seen_normalized.add(normalized_title)
    return unique_titles


async def extract_reference_titles(
    llm_config: NodeLLMConfig,
    llm_client: LangChainClient,
    arxiv_full_text_list: list[str],
) -> list[list[str]]:
    async def _extract_for_paper(paper_idx: int, full_text: str) -> list[str]:
        if not full_text:
            logger.warning(
                f"Empty full_text encountered for paper {paper_idx}; skipping"
            )
            return []
        refs = await _extract_references_from_text(
            full_text=full_text,
            template=extract_reference_titles_prompt,
            llm_client=llm_client,
            llm_config=llm_config,
            context_label=f"paper-{paper_idx}",
        )
        return _deduplicate_titles(refs)

    reference_list: list[list[str]] = list(
        await asyncio.gather(
            *(
                _extract_for_paper(idx, text)
                for idx, text in enumerate(arxiv_full_text_list)
            )
        )
    )

    total_references = sum(len(refs) for refs in reference_list)
    logger.info(f"Extracted {total_references} reference titles across all papers")

    return reference_list
