import logging
import re
from datetime import datetime

import bibtexparser
from bibtexparser.bibdatabase import BibDatabase

from airas.core.types.research_study import ResearchStudy
from airas.research_record.render.render_references_bib import unique_bibkey

logger = logging.getLogger(__name__)

_EARLIEST_PLAUSIBLE_YEAR = 1800
_DOI_PATTERN = re.compile(r"^10\.\d{4,9}/\S+$")
_ARXIV_ID_IN_URL_PATTERN = re.compile(
    r"arxiv\.org/(?:abs|pdf)/([^\s/?#]+)", re.IGNORECASE
)
_ARXIV_ID_IN_DOI_PATTERN = re.compile(r"^10\.48550/arxiv\.(\S+)$", re.IGNORECASE)


def _normalize_arxiv_id(arxiv_id: str) -> str:
    normalized = arxiv_id.strip().lower()
    normalized = re.sub(r"^arxiv[:/]", "", normalized)
    normalized = re.sub(r"\.pdf$", "", normalized)
    normalized = re.sub(r"v\d+$", "", normalized)
    return normalized


def _extract_year(published_date) -> str | None:
    if not published_date:
        return None
    year_match = re.match(r"(\d{4})", str(published_date).strip())
    return year_match.group(1) if year_match else None


def _validate_research_study(
    ref: ResearchStudy, title: str, authors: list[str], year: str | None
) -> list[str]:
    """Return human-readable descriptions of every inconsistency found.

    Detection is deliberately limited to what can be checked from the record
    itself; no network lookups are performed here.
    """
    problems: list[str] = []
    meta_data = ref.meta_data

    if year:
        current_year = datetime.now().year
        year_value = int(year)
        if year_value < _EARLIEST_PLAUSIBLE_YEAR or year_value > current_year + 1:
            problems.append(f"implausible publication year {year!r}")
    elif meta_data.published_date:
        problems.append(
            f"published_date {meta_data.published_date!r} has no parsable year"
        )

    arxiv_id = meta_data.arxiv_id
    if arxiv_id:
        normalized_arxiv_id = _normalize_arxiv_id(arxiv_id)
        for field_name, raw_value, pattern in (
            ("pdf_url", meta_data.pdf_url, _ARXIV_ID_IN_URL_PATTERN),
            ("doi", meta_data.doi, _ARXIV_ID_IN_DOI_PATTERN),
        ):
            if not raw_value:
                continue
            match = pattern.search(raw_value.strip())
            if match and _normalize_arxiv_id(match.group(1)) != normalized_arxiv_id:
                problems.append(
                    f"arxiv_id {arxiv_id!r} disagrees with {field_name} {raw_value!r} "
                    "(the record may merge two different papers)"
                )

    if meta_data.doi and not _DOI_PATTERN.match(meta_data.doi.strip()):
        problems.append(f"doi {meta_data.doi!r} is not a well-formed DOI")

    if meta_data.github_url and "github.com" not in meta_data.github_url.lower():
        problems.append(f"github_url {meta_data.github_url!r} is not a GitHub URL")

    if meta_data.authors and not authors:
        problems.append("every author entry is blank")

    if not title:
        problems.append("title is empty")
    elif not authors and not year:
        problems.append("neither authors nor a publication year are available")

    return problems


def _is_emittable(title: str, authors: list[str], year: str | None) -> bool:
    # A BibTeX entry without a title, or with neither author nor year, is
    # rejected by most styles and can break the whole bibliography, so such a
    # record is dropped rather than emitted.
    return bool(title) and bool(authors or year)


def generate_bibfile(
    research_study_list: list[ResearchStudy],
) -> str:
    if not research_study_list:
        return ""

    taken: set[str] = set()
    db_research = BibDatabase()

    for i, ref in enumerate(research_study_list):
        entry = _generate_bibfile_entry(ref, i, taken)
        if entry is None:
            continue
        taken.add(entry["ID"])
        db_research.entries.append(entry)

    return bibtexparser.dumps(db_research).strip()


def _generate_bibfile_entry(
    ref: ResearchStudy, index: int, taken: set[str]
) -> dict | None:
    meta_data = ref.meta_data

    title = (ref.title or "").strip()
    authors = [a.strip() for a in (meta_data.authors or []) if a and a.strip()]
    published_date = meta_data.published_date if meta_data is not None else None

    year = _extract_year(published_date)

    problems = _validate_research_study(ref, title, authors, year)
    study_label = title or f"<untitled study at index {index}>"
    if problems:
        logger.warning(
            f"Inconsistent bibliography record for {study_label!r}: "
            f"{'; '.join(problems)}."
        )

    if not _is_emittable(title, authors, year):
        logger.warning(
            f"Skipping bibliography entry for {study_label!r}: the record would "
            "produce a malformed BibTeX entry."
        )
        return None

    citation_key = unique_bibkey(title, authors, year, taken)
    if citation_key != unique_bibkey(title, authors, year, set()):
        logger.warning(
            f"Citation key collision for {study_label!r}; emitting it as {citation_key!r}."
        )

    entry = {
        "ID": citation_key,
        "ENTRYTYPE": "article",  # Default to article, could be made configurable
    }

    entry["title"] = title

    if authors:
        entry["author"] = " and ".join(authors)

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
