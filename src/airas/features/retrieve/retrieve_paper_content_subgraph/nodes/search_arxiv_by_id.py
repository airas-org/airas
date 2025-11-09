from logging import getLogger

import feedparser

from airas.services.api_client.arxiv_client import ArxivClient
from airas.types.arxiv import ArxivInfo
from airas.types.research_study import MetaData, ResearchStudy

logger = getLogger(__name__)


def search_arxiv_by_id(
    research_study_list: list[ResearchStudy],
    arxiv_client: ArxivClient,
) -> list[ResearchStudy]:
    for research_study in research_study_list:
        arxiv_id = (
            research_study.meta_data.arxiv_id if research_study.meta_data else None
        )
        if not arxiv_id:
            continue

        try:
            xml_feed = arxiv_client.get_paper_by_id(arxiv_id=arxiv_id.strip())
        except Exception as e:
            logger.error(
                f"Failed to process arXiv ID {arxiv_id}: {e}. Skipping to the next."
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
            title=entry.title or "No Title",
            authors=[a.name for a in getattr(entry, "authors", [])],
            published_date=getattr(entry, "published", ""),
            summary=getattr(entry, "summary", ""),
            journal=getattr(entry, "arxiv_journal_ref", None),
            doi=getattr(entry, "arxiv_doi", None),
        )

        if not research_study.meta_data:
            research_study.meta_data = MetaData()

        research_study.meta_data.arxiv_id = arxiv_info.id
        research_study.meta_data.doi = arxiv_info.doi
        research_study.meta_data.authors = arxiv_info.authors
        research_study.meta_data.published_date = arxiv_info.published_date
        research_study.meta_data.venue = arxiv_info.journal
        research_study.meta_data.pdf_url = f"https://arxiv.org/pdf/{arxiv_info.id}.pdf"

        if arxiv_info.summary:
            research_study.abstract = arxiv_info.summary

    return research_study_list


if __name__ == "__main__":
    research_study = ResearchStudy(
        title="Attention Is All You Need", meta_data=MetaData(arxiv_id="1706.03762")
    )
    results = search_arxiv_by_id([research_study])
    print(f"results: {results[0].model_dump() if results else 'No results'}")
