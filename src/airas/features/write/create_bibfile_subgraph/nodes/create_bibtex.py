import logging
import re

import bibtexparser
from bibtexparser.bibdatabase import BibDatabase

from airas.types.research_study import ResearchStudy

logger = logging.getLogger(__name__)


REQUIRED_CITATIONS_MARKER = "REQUIRED CITATIONS"
REFERENCE_CANDIDATES_MARKER = "REFERENCE CANDIDATES"


def _generate_citation_key(title: str, authors: list[str], year) -> str:
    first_author = ""
    if authors and len(authors) > 0:
        author_parts = authors[0].split()
        first_author = author_parts[-1].lower() if author_parts else "author"
    else:
        first_author = "author"

    year_str = str(year) if year else "year"

    title_words = re.findall(r"\b[a-zA-Z]{3,}\b", title.lower()) if title else []
    first_word = title_words[0] if title_words else "title"

    first_author = re.sub(r"[^a-z0-9]", "", first_author)
    first_word = re.sub(r"[^a-z0-9]", "", first_word)

    citation_key = f"{first_author}_{year_str}_{first_word}"
    return citation_key


def create_bibtex(
    research_study_list: list[ResearchStudy],
    reference_research_study_list: list[ResearchStudy],
) -> str:
    if not research_study_list and not reference_research_study_list:
        return ""

    bibtex_sections = []

    # Research papers section
    if research_study_list:
        bibtex_sections.append("% ===========================================")
        bibtex_sections.append(f"% {REQUIRED_CITATIONS_MARKER}")
        bibtex_sections.append("% These papers must be cited in the manuscript")
        bibtex_sections.append("% ===========================================")
        bibtex_sections.append("")

        db_research = BibDatabase()
        for i, ref in enumerate(research_study_list):
            entry = _create_bibtex_entry(ref, i)
            db_research.entries.append(entry)

        research_bibtex = bibtexparser.dumps(db_research).strip()
        bibtex_sections.append(research_bibtex)
        bibtex_sections.append("")

    # Reference papers section
    if reference_research_study_list:
        bibtex_sections.append("% ===========================================")
        bibtex_sections.append(f"% {REFERENCE_CANDIDATES_MARKER}")
        bibtex_sections.append("% Additional reference papers for context")
        bibtex_sections.append("% ===========================================")
        bibtex_sections.append("")

        db_reference = BibDatabase()
        for i, ref in enumerate(reference_research_study_list):
            entry = _create_bibtex_entry(ref, i + len(research_study_list))
            db_reference.entries.append(entry)

        reference_bibtex = bibtexparser.dumps(db_reference).strip()
        bibtex_sections.append(reference_bibtex)

    return "\n".join(bibtex_sections)


def _create_bibtex_entry(ref: ResearchStudy, index: int) -> dict:
    meta_data = ref.meta_data or {}

    title = ref.title or f"ref{index}"
    authors = getattr(meta_data, "authors", None) or []
    year = getattr(meta_data, "published_date", None)

    citation_key = _generate_citation_key(title, authors, year)

    entry = {
        "ID": citation_key,
        "ENTRYTYPE": "article",  # Default to article, could be made configurable
    }

    if title:
        entry["title"] = title

    if authors:
        if isinstance(authors, list):
            entry["author"] = " and ".join(authors)
        else:
            entry["author"] = str(authors)

    if year:
        entry["year"] = str(year)

    if abstract := ref.abstract or "":
        entry["abstract"] = abstract

    if journal := getattr(meta_data, "venue", None):
        entry["journal"] = journal

    if volume := getattr(meta_data, "volume", None):
        entry["volume"] = str(volume)

    if number := getattr(meta_data, "issue", None):
        entry["number"] = str(number)

    if pages := getattr(meta_data, "pages", None):
        entry["pages"] = str(pages)

    if doi := getattr(meta_data, "doi", None):
        entry["doi"] = doi

    if arxiv_url := getattr(meta_data, "pdf_url", None):
        entry["arxiv_url"] = arxiv_url

    if github_url := getattr(meta_data, "github_url", None):
        entry["github_url"] = github_url

    return entry


def main():
    test_research_study_list = [
        {
            "title": "Attention Is All You Need",
            "authors": ["Vaswani, Ashish", "Shazeer, Noam"],
            "published_year": 2017,
            "abstract": "The dominant sequence transduction models are based on complex recurrent or convolutional neural networks.",
            "meta_data": {
                "authors": ["Vaswani, Ashish", "Shazeer, Noam", "Parmar, Niki"],
                "published_year": 2017,
                "journal": "Neural Information Processing Systems",
                "volume": "30",
                "pages": "5998-6008",
                "doi": "10.48550/arXiv.1706.03762",
                "arxiv_url": "https://arxiv.org/abs/1706.03762",
            },
        },
    ]

    test_reference_study_list = [
        {
            "title": "BERT: Pre-training of Deep Bidirectional Transformers for Language Understanding",
            "authors": ["Devlin, Jacob", "Chang, Ming-Wei"],
            "published_year": 2018,
            "abstract": "We introduce BERT, which stands for Bidirectional Encoder Representations from Transformers.",
            "meta_data": {
                "authors": ["Devlin, Jacob", "Chang, Ming-Wei", "Lee, Kenton"],
                "published_year": 2018,
                "journal": "arXiv preprint",
                "volume": "abs/1810.04805",
                "number": "1810.04805",
                "pages": "1-16",
                "arxiv_url": "https://arxiv.org/abs/1810.04805",
                "github_url": "https://github.com/google-research/bert",
            },
        },
    ]

    try:
        bibtex_output = create_bibtex(
            test_research_study_list, test_reference_study_list
        )
        print("Generated BibTeX:")
        print(bibtex_output)
    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    main()
