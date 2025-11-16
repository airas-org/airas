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

    citation_key = f"{first_author}-{year_str}-{first_word}"
    return citation_key


def create_bibtex(
    research_study_list: list[ResearchStudy],
    reference_research_study_list: list[ResearchStudy],
) -> str:
    if not research_study_list and not reference_research_study_list:
        return ""

    bibtex_sections = []
    seen_citation_keys = set()

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
            citation_key = entry["ID"]
            if citation_key not in seen_citation_keys:
                db_research.entries.append(entry)
                seen_citation_keys.add(citation_key)

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
            citation_key = entry["ID"]
            if citation_key not in seen_citation_keys:
                db_reference.entries.append(entry)
                seen_citation_keys.add(citation_key)

        reference_bibtex = bibtexparser.dumps(db_reference).strip()
        bibtex_sections.append(reference_bibtex)

    return "\n".join(bibtex_sections)


def _create_bibtex_entry(ref: ResearchStudy, index: int) -> dict:
    meta_data = ref.meta_data or {}

    title = ref.title or f"ref{index}"
    authors = getattr(meta_data, "authors", None) or []
    published_date = getattr(meta_data, "published_date", None)

    year = None
    if published_date:
        year_match = re.match(r"(\d{4})", str(published_date))
        year = year_match.group(1) if year_match else published_date

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
