from logging import getLogger
from typing import Any

import bibtexparser

logger = getLogger(__name__)


def parse_bibtex_to_dict(references_bib: str) -> dict[str, dict[str, Any]]:
    try:
        db = bibtexparser.loads(references_bib)
        references = {}
        for entry in db.entries:
            citation_key = entry.get("ID", "")
            if citation_key:
                references[citation_key] = entry
        return references
    except Exception as e:
        logger.warning(f"Failed to parse BibTeX: {e}")
        return {}
