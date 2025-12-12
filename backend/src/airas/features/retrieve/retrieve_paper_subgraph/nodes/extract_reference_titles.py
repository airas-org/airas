import asyncio
import string
from collections.abc import Awaitable
from logging import getLogger

from jinja2 import Environment
from pydantic import BaseModel

from airas.features.retrieve.retrieve_paper_subgraph.prompt.extract_reference_titles_prompt import (
    extract_reference_titles_prompt,
)
from airas.services.api_client.langchain_client import LangChainClient
from airas.services.api_client.llm_specs import LLM_MODELS

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
    llm_name: LLM_MODELS,
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
        output, _ = await llm_client.structured_outputs(
            message=messages,
            data_model=LLMOutput,
            llm_name=llm_name,
        )
    except Exception as e:
        logger.error(f"Error extracting references for {context_label}: {e}")
        return []

    if output is None or not isinstance(output, dict):
        logger.warning(
            "Warning: No valid response from LLM for reference extraction for "
            f"{context_label}."
        )
        return []
    reference_titles = output.get("reference_titles", [])
    logger.info(
        "Found %s reference titles for %s.",
        len(reference_titles),
        context_label,
    )

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
    llm_name: LLM_MODELS,
    llm_client: LangChainClient,
    arxiv_full_text_list: list[list[str]],
) -> list[list[list[str]]]:
    reference_groups: list[list[list[str]]] = [
        [[] for _ in text_group] for text_group in arxiv_full_text_list
    ]

    tasks: list[Awaitable[list[str]]] = []
    task_indices: list[tuple[int, int]] = []

    for group_idx, text_group in enumerate(arxiv_full_text_list):
        for paper_idx, full_text in enumerate(text_group):
            if not full_text:
                logger.warning(
                    "Empty full_text encountered for group %s paper %s; skipping",
                    group_idx,
                    paper_idx,
                )
                continue
            task_indices.append((group_idx, paper_idx))
            tasks.append(
                _extract_references_from_text(
                    full_text=full_text,
                    template=extract_reference_titles_prompt,
                    llm_client=llm_client,
                    llm_name=llm_name,
                    context_label=f"group-{group_idx}-paper-{paper_idx}",
                )
            )

    if not tasks:
        logger.warning("No valid full_text values provided for reference extraction")
        return reference_groups

    results = await asyncio.gather(*tasks)
    for (group_idx, paper_idx), reference_titles in zip(
        task_indices, results, strict=True
    ):
        reference_groups[group_idx][paper_idx] = _deduplicate_titles(reference_titles)

    total_references = sum(
        len(reference_titles)
        for group in reference_groups
        for reference_titles in group
    )
    logger.info("Extracted %s reference titles across all papers", total_references)

    return reference_groups
