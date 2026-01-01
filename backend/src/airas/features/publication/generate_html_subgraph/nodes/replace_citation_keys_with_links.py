import re
from logging import getLogger
from typing import Any

from airas.utils.parse_bibtex_to_dict import parse_bibtex_to_dict

logger = getLogger(__name__)


def replace_citation_keys_with_links(html_text: str, references_bib: str) -> str:
    references = parse_bibtex_to_dict(references_bib)

    def replace_citation(match):
        content = match.group(1)

        if "," not in content:
            if content in references:
                return _create_citation_link(content, references[content])
            else:
                logger.info(
                    f"Citation key not found in references, ignoring: {content}"
                )
                return ""

        keys = [key.strip() for key in content.split(",")]
        valid_links = []
        for key in keys:
            if key in references:
                valid_links.append(_create_citation_link(key, references[key]))
            else:
                logger.info(f"Citation key not found in references, ignoring: {key}")

        if not valid_links:
            return ""

        return ", ".join(valid_links)

    citation_pattern = r"\[([^\[\]]+)\]"
    html_text = re.sub(citation_pattern, replace_citation, html_text)

    return html_text


def _create_citation_link(citation_key: str, ref: dict[str, Any]) -> str:
    if ref.get("arxiv_url"):
        link = ref["arxiv_url"]
    elif ref.get("doi"):
        link = f"https://doi.org/{ref['doi']}"
    elif ref.get("github_url"):
        link = ref["github_url"]
    else:
        link = f"#ref-{citation_key}"

    title = ref.get("title", citation_key)
    author = ref.get("author", "")
    if author:
        first_author = author.split(" and ")[0].split(",")[0].strip()
        display_text = f"({first_author}, {ref.get('year', 'n.d.')})"
    else:
        display_text = f"({citation_key})"

    return f'<a href="{link}" target="_blank" title="{title}">{display_text}</a>'
