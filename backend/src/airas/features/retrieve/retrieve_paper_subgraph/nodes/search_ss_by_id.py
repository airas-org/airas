from logging import getLogger

from airas.services.api_client.semantic_scholar_client import SemanticScholarClient
from airas.types.research_study import MetaData, ResearchStudy
from airas.types.semantic_scholar import SemanticScholarInfo

logger = getLogger(__name__)


def search_ss_by_id(
    research_study_list: list[ResearchStudy],
    ss_client: SemanticScholarClient,
) -> list[ResearchStudy]:
    for research_study in research_study_list:
        arxiv_id = (
            research_study.meta_data.arxiv_id if research_study.meta_data else None
        )
        if not arxiv_id:
            continue

        fields = (
            "paperId",
            "title",
            "abstract",
            "year",
            "authors",
            "venue",
            "externalIds",
            "openAccessPdf",
            "publicationTypes",
            "publicationDate",
            "journal",
            "citationCount",
            "referenceCount",
            "influentialCitationCount",
            "isOpenAccess",
        )
        try:
            response_data = ss_client.get_paper_by_arxiv_id(
                arxiv_id=arxiv_id.strip(), fields=fields
            )
        except Exception as e:
            logger.error(
                f"Failed to process arXiv ID {arxiv_id}: {e}. Skipping to the next."
            )
            continue

        if not response_data:
            continue

        external_ids = response_data.get("externalIds", {})
        authors = [
            author.get("name", "")
            for author in response_data.get("authors", [])
            if author.get("name")
        ]
        journal_data = response_data.get("journal", {})
        open_access_pdf = response_data.get("openAccessPdf", {})

        ss_info = SemanticScholarInfo(
            title=response_data.get("title", "No Title"),
            abstract=response_data.get("abstract"),
            authors=authors,
            publication_types=response_data.get("publicationTypes", []),
            year=response_data.get("year"),
            publication_date=response_data.get("publicationDate"),
            venue=response_data.get("venue"),
            journal_name=journal_data.get("name") if journal_data else None,
            journal_volume=journal_data.get("volume") if journal_data else None,
            journal_pages=journal_data.get("pages") if journal_data else None,
            external_ids=external_ids,
            citation_count=response_data.get("citationCount"),
            reference_count=response_data.get("referenceCount"),
            influential_citation_count=response_data.get("influentialCitationCount"),
            is_open_access=response_data.get("isOpenAccess"),
            open_access_pdf_url=open_access_pdf.get("url") if open_access_pdf else None,
        )

        if not research_study.meta_data:
            research_study.meta_data = MetaData()

        research_study.meta_data.arxiv_id = ss_info.external_ids.get("ArXiv")
        research_study.meta_data.doi = ss_info.external_ids.get("DOI")

        research_study.meta_data.authors = ss_info.authors
        research_study.meta_data.published_date = (
            str(ss_info.year) if ss_info.year else ss_info.publication_date
        )
        research_study.meta_data.venue = ss_info.venue

        if ss_info.journal_volume:
            research_study.meta_data.volume = ss_info.journal_volume
        if ss_info.journal_pages:
            research_study.meta_data.pages = ss_info.journal_pages

        research_study.meta_data.citation_count = ss_info.citation_count
        research_study.meta_data.reference_count = ss_info.reference_count

        if ss_info.is_open_access is not None:
            research_study.meta_data.access_type = (
                "free" if ss_info.is_open_access else "paid"
            )

        if ss_info.open_access_pdf_url:
            research_study.meta_data.pdf_url = ss_info.open_access_pdf_url
        elif research_study.meta_data.arxiv_id:
            research_study.meta_data.pdf_url = (
                f"https://arxiv.org/pdf/{research_study.meta_data.arxiv_id}.pdf"
            )

        if ss_info.abstract:
            research_study.abstract = ss_info.abstract

    return research_study_list


if __name__ == "__main__":
    research_study = ResearchStudy(
        title="Attention Is All You Need", meta_data=MetaData(arxiv_id="1706.03762")
    )
    results = search_ss_by_id([research_study])
    print(f"results: {results[0].model_dump() if results else 'No results'}")
