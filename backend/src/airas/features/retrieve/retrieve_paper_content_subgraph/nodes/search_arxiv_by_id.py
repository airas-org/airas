from logging import getLogger

import feedparser

from airas.services.api_client.arxiv_client import ArxivClient
from airas.types.arxiv import ArxivInfo

logger = getLogger(__name__)


def search_arxiv_by_id(
    arxiv_id_list: list[list[str]],
    arxiv_client: ArxivClient,
) -> list[list[ArxivInfo]]:
    """
    Fetch arXiv information for batched ID groups while preserving their structure.
    """

    arxiv_info_groups: list[list[ArxivInfo]] = []

    for arxiv_id_group in arxiv_id_list:
        group_results: list[ArxivInfo] = []

        for raw_arxiv_id in arxiv_id_group:
            if not raw_arxiv_id:
                continue

            try:
                xml_feed = arxiv_client.get_paper_by_id(arxiv_id=raw_arxiv_id.strip())
            except Exception as e:  # pragma: no cover - network/HTTP errors
                logger.error(
                    f"Failed to process arXiv ID {raw_arxiv_id}: {e}. Skipping to the next."
                )
                continue

            feed = feedparser.parse(xml_feed)
            if not feed.entries:
                continue

            entry = feed.entries[0]
            if not hasattr(entry, "id"):
                continue

            arxiv_info = ArxivInfo(
                id=entry.id.split("/")[-1],
                title=getattr(entry, "title", "") or "No Title",
                authors=[a.name for a in getattr(entry, "authors", [])],
                published_date=getattr(entry, "published", ""),
                summary=getattr(entry, "summary", ""),
                journal=getattr(entry, "arxiv_journal_ref", None),
                doi=getattr(entry, "arxiv_doi", None),
            )

            group_results.append(arxiv_info)

        arxiv_info_groups.append(group_results)

    return arxiv_info_groups
