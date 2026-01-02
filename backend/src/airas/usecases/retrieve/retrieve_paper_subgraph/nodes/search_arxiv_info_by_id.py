import asyncio
from logging import getLogger

import feedparser

from airas.core.types.arxiv import ArxivInfo
from airas.infra.arxiv_client import ArxivClient

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
    arxiv_id_list: list[str],
    arxiv_client: ArxivClient,
) -> list[ArxivInfo]:
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

    arxiv_info_list: list[ArxivInfo] = list(
        await asyncio.gather(
            *(_build_arxiv_info(arxiv_id) for arxiv_id in arxiv_id_list)
        )
    )

    return arxiv_info_list
