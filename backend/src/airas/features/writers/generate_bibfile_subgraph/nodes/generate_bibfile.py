import logging
import re

import bibtexparser
from bibtexparser.bibdatabase import BibDatabase

from airas.types.research_study import ResearchStudy

logger = logging.getLogger(__name__)


def _generate_citation_key(title: str, authors: list[str], year) -> str:
    first_author = ""
    if authors:
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


def generate_bibfile(
    research_study_list: list[ResearchStudy],
) -> str:
    if not research_study_list:
        return ""

    seen_citation_keys = set()
    db_research = BibDatabase()

    for i, ref in enumerate(research_study_list):
        entry = _generate_bibfile_entry(ref, i)
        citation_key = entry["ID"]
        if citation_key not in seen_citation_keys:
            db_research.entries.append(entry)
            seen_citation_keys.add(citation_key)

    return bibtexparser.dumps(db_research).strip()


def _generate_bibfile_entry(ref: ResearchStudy, index: int) -> dict:
    meta_data = ref.meta_data

    title = ref.title or f"ref{index}"
    authors = meta_data.authors or []
    published_date = meta_data.published_date if meta_data is not None else None

    year = None
    if published_date:
        year_match = re.match(r"(\d{4})", str(published_date))
        year = year_match.group(1) if year_match else None

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

    if journal := meta_data.venue:
        entry["journal"] = journal

    if volume := meta_data.volume:
        entry["volume"] = str(volume)

    if number := meta_data.issue:
        entry["number"] = str(number)

    if pages := meta_data.pages:
        entry["pages"] = str(pages)

    if doi := meta_data.doi:
        entry["doi"] = doi

    if arxiv_url := meta_data.pdf_url:
        entry["arxiv_url"] = arxiv_url

    if github_url := meta_data.github_url:
        entry["github_url"] = github_url

    return entry
