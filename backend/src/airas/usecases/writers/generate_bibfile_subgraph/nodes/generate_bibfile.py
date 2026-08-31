import logging
import re
from datetime import datetime

import bibtexparser
from bibtexparser.bibdatabase import BibDatabase

from airas.core.types.research_study import ResearchStudy

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


def _extract_surname(author: str) -> str:
    # Sources disagree on author formatting: OpenAlex/arXiv return
    # "Ashish Vaswani" while Semantic Scholar can return "Vaswani, Ashish".
    author = author.strip()
    if "," in author:
        surname = author.split(",", 1)[0]
    else:
        parts = author.split()
        surname = parts[-1] if parts else ""
    return surname.lower()


def _generate_citation_key(title: str, authors: list[str], year) -> str:
    first_author = ""
    if authors:
        first_author = _extract_surname(authors[0]) or "author"
    else:
        first_author = "author"

    year_str = str(year) if year else "year"

    title_words = re.findall(r"\b[a-zA-Z]{3,}\b", title.lower()) if title else []
    first_word = title_words[0] if title_words else "title"

    first_author = re.sub(r"[^a-z0-9]", "", first_author) or "author"
    first_word = re.sub(r"[^a-z0-9]", "", first_word) or "title"

    citation_key = f"{first_author}-{year_str}-{first_word}"
    return citation_key


def _disambiguation_suffix(occurrence: int) -> str:
    suffix = ""
    while occurrence > 0:
        occurrence, remainder = divmod(occurrence - 1, 26)
        suffix = chr(ord("a") + remainder) + suffix
    return suffix


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

    seen_citation_keys: dict[str, str] = {}
    db_research = BibDatabase()

    for i, ref in enumerate(research_study_list):
        entry = _generate_bibfile_entry(ref, i)
        if entry is None:
            continue

        base_key = entry["ID"]
        title = entry.get("title", "")
        if base_key in seen_citation_keys:
            occurrence = 1
            citation_key = f"{base_key}{_disambiguation_suffix(occurrence)}"
            while citation_key in seen_citation_keys:
                occurrence += 1
                citation_key = f"{base_key}{_disambiguation_suffix(occurrence)}"
            logger.warning(
                f"Citation key collision on {base_key!r} between "
                f"{seen_citation_keys[base_key]!r} and {title!r}; "
                f"emitting the latter as {citation_key!r}."
            )
            entry["ID"] = citation_key
        else:
            citation_key = base_key

        db_research.entries.append(entry)
        seen_citation_keys[citation_key] = title

    return bibtexparser.dumps(db_research).strip()


def _generate_bibfile_entry(ref: ResearchStudy, index: int) -> dict | None:
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

    citation_key = _generate_citation_key(title, authors, year)

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
