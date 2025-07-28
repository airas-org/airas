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


def create_bibtex(references: list[dict]) -> str:
    if not references:
        return ""

    db = BibDatabase()

    for i, ref in enumerate(references):
        meta_data = ref.get("meta_data", {})

        title = ref.get("title", f"ref{i}")
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

        db.entries.append(entry)

    bibtex_str = bibtexparser.dumps(db)
    return bibtex_str


def main():
    # Test data
    test_references = [
        {
            "title": "Attention Is All You Need",
            "authors": ["Vaswani, Ashish", "Shazeer, Noam"],
            "published_year": 2017,
            "journal": "Neural Information Processing Systems",
            "abstract": "The dominant sequence transduction models are based on complex recurrent or convolutional neural networks.",
            "doi": "10.48550/arXiv.1706.03762",
        },
        {
            "title": "BERT: Pre-training of Deep Bidirectional Transformers for Language Understanding",
            "authors": ["Devlin, Jacob", "Chang, Ming-Wei"],
            "published_year": 2018,
            "abstract": "We introduce BERT, which stands for Bidirectional Encoder Representations from Transformers.",
            "arxiv_url": "https://arxiv.org/abs/1810.04805",
        },
    ]

    try:
        bibtex_output = create_bibtex(test_references)
        print("Generated BibTeX:")
        print(bibtex_output)
    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    main()
