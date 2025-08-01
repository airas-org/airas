import logging
import re

import bibtexparser
from bibtexparser.bibdatabase import BibDatabase

logger = logging.getLogger(__name__)


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
    research_study_list: list[dict], reference_study_list: list[dict]
) -> str:
    if not research_study_list and not reference_study_list:
        return ""

    bibtex_sections = []

    # Research papers section
    if research_study_list:
        bibtex_sections.append("% ===========================================")
        bibtex_sections.append("% REQUIRED CITATIONS")
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
    if reference_study_list:
        bibtex_sections.append("% ===========================================")
        bibtex_sections.append("% REFERENCE CANDIDATES")
        bibtex_sections.append("% Additional reference papers for context")
        bibtex_sections.append("% ===========================================")
        bibtex_sections.append("")

        db_reference = BibDatabase()
        for i, ref in enumerate(reference_study_list):
            entry = _create_bibtex_entry(ref, i + len(research_study_list))
            db_reference.entries.append(entry)

        reference_bibtex = bibtexparser.dumps(db_reference).strip()
        bibtex_sections.append(reference_bibtex)

    return "\n".join(bibtex_sections)


def _create_bibtex_entry(ref: dict, index: int) -> dict:
    meta_data = ref.get("meta_data", {})

    title = ref.get("title", f"ref{index}")
    authors = ref.get("authors") or meta_data.get("authors", [])
    year = ref.get("published_year") or meta_data.get("published_year")

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

    if abstract := ref.get("abstract", ""):
        entry["abstract"] = abstract

    if journal := meta_data.get("journal") or ref.get("journal"):
        entry["journal"] = journal

    if volume := meta_data.get("volume") or ref.get("volume"):
        entry["volume"] = str(volume)

    if number := meta_data.get("number") or ref.get("number"):
        entry["number"] = str(number)

    if pages := meta_data.get("pages") or ref.get("pages"):
        entry["pages"] = str(pages)

    if doi := meta_data.get("doi") or ref.get("doi"):
        entry["doi"] = doi

    if arxiv_url := meta_data.get("arxiv_url") or ref.get("arxiv_url"):
        entry["arxiv_url"] = arxiv_url

    if github_url := meta_data.get("github_url") or ref.get("github_url"):
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
