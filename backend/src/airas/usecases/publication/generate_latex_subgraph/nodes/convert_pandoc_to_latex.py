import re

from airas.core.types.paper import PaperContent
from airas.usecases.publication.nodes.parse_bibtex_to_dict import parse_bibtex_to_dict

# ---------------------------------------------------------------------------
# Figure patterns
# ---------------------------------------------------------------------------

# ![Caption](filepath){#fig:label}
_FIGURE_PATTERN = re.compile(r"!\[([^\]]*)\]\(([^)]+)\)\{#([^}]+)\}")

# @fig:label  (stops at whitespace, comma, period, ), }, ])
_FIGURE_REF_PATTERN = re.compile(r"@(fig:[^\s,.)}\]]+)")


def _build_figure_env(caption: str, filepath: str, label: str) -> str:
    # LLM sometimes escapes underscores in file paths (e.g. foo\_bar.pdf); undo that.
    filepath = filepath.replace(r"\_", "_")
    return (
        f"\\begin{{figure}}[H]\n"
        f"\\centering\n"
        f"\\includegraphics[width=0.7\\linewidth]{{{filepath}}}\n"
        f"\\caption{{{caption}}}\n"
        f"\\label{{{label}}}\n"
        f"\\end{{figure}}"
    )


def _convert_figures(text: str) -> str:
    text = _FIGURE_PATTERN.sub(
        lambda m: _build_figure_env(m.group(1), m.group(2), m.group(3)),
        text,
    )
    text = _FIGURE_REF_PATTERN.sub(
        lambda m: f"Figure~\\ref{{{m.group(1)}}}",
        text,
    )
    return text


# ---------------------------------------------------------------------------
# Citation patterns
# ---------------------------------------------------------------------------


def _convert_citation_format(
    content: str, references_bib_dict: dict[str, dict[str, str]]
) -> str:
    citation_entries = [entry.strip() for entry in content.split(";")]

    citation_keys = []
    optional_arg = None

    for entry in citation_entries:
        entry = entry.lstrip("@").strip()

        match = re.match(r"([^,]+)\s*,\s*(.+)", entry)
        key = match.group(1).strip() if match else entry
        if match and optional_arg is None:
            optional_arg = match.group(2).strip()

        if key in references_bib_dict:
            citation_keys.append(key)

    if not citation_keys:
        return ""

    keys_str = ",".join(citation_keys)
    return (
        f"\\cite[{optional_arg}]{{{keys_str}}}"
        if optional_arg
        else f"\\cite{{{keys_str}}}"
    )


def _convert_citations(
    text: str, references_bib_dict: dict[str, dict[str, str]]
) -> str:
    return re.sub(
        r"\[@([^\]]+)\]",
        lambda m: _convert_citation_format(m.group(1), references_bib_dict),
        text,
    )


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def convert_pandoc_to_latex(
    paper_content: PaperContent, references_bib: str
) -> PaperContent:
    """
    Convert all Pandoc/Quarto syntax to LaTeX before the LLM conversion step.

    Citations:
    - [@key] → \\cite{key}
    - [@key1; @key2] → \\cite{key1,key2}
    - [@key, p. 23] → \\cite[p. 23]{key}

    Figures:
    - ![Caption](images/file.pdf){#fig:label} → \\begin{figure}[H]...\\end{figure}
    - @fig:label → Figure~\\ref{fig:label}
    """
    references_bib_dict = parse_bibtex_to_dict(references_bib)

    converted = {}
    for field in PaperContent.model_fields.keys():
        text = getattr(paper_content, field)
        if text:
            text = _convert_figures(text)
            text = _convert_citations(text, references_bib_dict)
        converted[field] = text

    return PaperContent(**converted)
