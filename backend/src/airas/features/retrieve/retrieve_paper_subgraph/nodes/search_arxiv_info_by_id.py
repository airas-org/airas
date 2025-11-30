import asyncio
from collections.abc import Coroutine
from logging import getLogger
from typing import Any

import feedparser

from airas.services.api_client.arxiv_client import ArxivClient
from airas.types.arxiv import ArxivInfo

logger = getLogger(__name__)


def _empty_arxiv_info(arxiv_id: str = "") -> ArxivInfo:
    return ArxivInfo(
        id=arxiv_id,
        title="",
        authors=[],
        published_date="",
        summary="",
        journal=None,
        doi=None,
        affiliation=None,
    )


async def search_arxiv_info_by_id(
    arxiv_id_list: list[list[str]],
    arxiv_client: ArxivClient,
) -> list[list[ArxivInfo]]:
    """
    Fetch arXiv information for batched ID groups while preserving their structure.
    """

    async def _build_arxiv_info(raw_arxiv_id: str) -> ArxivInfo:
        sanitized_id = (raw_arxiv_id or "").strip()
        if not sanitized_id:
            return _empty_arxiv_info()

        try:
            xml_feed = await arxiv_client.aget_paper_by_id(arxiv_id=sanitized_id)
        except Exception as e:  # pragma: no cover - network/HTTP errors
            logger.error(
                f"Failed to process arXiv ID {raw_arxiv_id}: {e}. Skipping to the next."
            )
            return _empty_arxiv_info(sanitized_id)

        feed = feedparser.parse(xml_feed)
        if not feed.entries:
            return _empty_arxiv_info(sanitized_id)

        entry = feed.entries[0]
        if not hasattr(entry, "id"):
            return _empty_arxiv_info(sanitized_id)

        return ArxivInfo(
            id=entry.id.split("/")[-1],
            title=getattr(entry, "title", "") or "No Title",
            authors=[a.name for a in getattr(entry, "authors", [])],
            published_date=getattr(entry, "published", ""),
            summary=getattr(entry, "summary", ""),
            journal=getattr(entry, "arxiv_journal_ref", None),
            doi=getattr(entry, "arxiv_doi", None),
            affiliation=getattr(entry, "arxiv_affiliation", None),
        )

    arxiv_info_groups: list[list[ArxivInfo]] = [
        [_empty_arxiv_info() for _ in arxiv_id_group]
        for arxiv_id_group in arxiv_id_list
    ]

    pending: list[tuple[int, int, Coroutine[Any, Any, ArxivInfo]]] = []
    for group_idx, arxiv_id_group in enumerate(arxiv_id_list):
        for item_idx, raw_arxiv_id in enumerate(arxiv_id_group):
            pending.append((group_idx, item_idx, _build_arxiv_info(raw_arxiv_id)))

    if not pending:
        return arxiv_info_groups

    results = await asyncio.gather(*(coro for _, _, coro in pending))
    for (group_idx, item_idx, _), arxiv_info in zip(pending, results, strict=True):
        arxiv_info_groups[group_idx][item_idx] = arxiv_info

    return arxiv_info_groups
