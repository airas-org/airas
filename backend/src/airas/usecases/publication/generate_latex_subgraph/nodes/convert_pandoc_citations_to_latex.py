import re

from airas.core.types.paper import ICLR2024PaperContent, PaperContent
from airas.usecases.publication.nodes.parse_bibtex_to_dict import parse_bibtex_to_dict


def convert_pandoc_citations_to_latex(
    paper_content: PaperContent, references_bib: str
) -> PaperContent:
    """
    Convert Pandoc/Quarto citation format to LaTeX citation format.

    Supported formats:
    - Single citation: [@vaswani-2017-attention] → \\cite{vaswani-2017-attention}
    - Multiple citations: [@vaswani-2017-attention; @devlin-2018-bert] → \\cite{vaswani-2017-attention,devlin-2018-bert}
    - With page numbers: [@vaswani-2017-attention, p. 23] → \\cite[p. 23]{vaswani-2017-attention}
    """
    references_bib_dict = parse_bibtex_to_dict(references_bib)

    def converter(text):
        return re.sub(
            r"\[@([^\]]+)\]",
            lambda match: _convert_citation_format(match.group(1), references_bib_dict),
            text,
        )

    converted_data = {
        field: converter(text) if text else text
        for field, text in paper_content.model_dump().items()
    }

    return ICLR2024PaperContent(**converted_data)


def _convert_citation_format(
    content: str, references_bib_dict: dict[str, dict[str, str]]
) -> str:
    citation_entries = [entry.strip() for entry in content.split(";")]

    citation_keys = []
    optional_arg = None

    for entry in citation_entries:
        entry = entry.lstrip("@").strip()

        # Check for optional arguments (page numbers, etc.)
        # Format: key, p. 23
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


if __name__ == "__main__":
    # Test Pandoc/Quarto citation format conversion
    paper_content = ICLR2024PaperContent(
        title="Test Paper Title",
        abstract="Abstract with single citation [@vaswani-2017-attention].",
        introduction=(
            "Introduction with various citation formats:\n"
            "- Single citation: [@vaswani-2017-attention]\n"
            "- Multiple citations: [@vaswani-2017-attention; @devlin-2018-bert]\n"
            "- With page number: [@vaswani-2017-attention, p. 23]\n"
            "- Mixed valid and invalid: [@vaswani-2017-attention; @missing-key]\n"
            "- Invalid only: [@missing-key]"
        ),
        related_work="Related work section.",
        background="Background section.",
        method="Method section.",
        experimental_setup="Experimental setup section.",
        results="Results section.",
        conclusion="Conclusion section.",
    )

    reference_bib = """
@article{vaswani-2017-attention,
 title = {Attention Is All You Need},
 author = {Vaswani, Ashish and others},
 year = {2017}
}

@article{devlin-2018-bert,
 title = {BERT: Pre-training of Deep Bidirectional Transformers for Language Understanding},
 author = {Devlin, Jacob and others},
 year = {2018}
}
"""

    result = convert_pandoc_citations_to_latex(paper_content, reference_bib)
    print("=" * 60)
    print("Abstract:")
    print(result.abstract)
    print("\n" + "=" * 60)
    print("Introduction:")
    print(result.introduction)
    print("=" * 60)
