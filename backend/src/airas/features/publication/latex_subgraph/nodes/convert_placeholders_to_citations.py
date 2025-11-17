import re

from airas.types.paper import PaperContent
from airas.utils.parse_bibtex_to_dict import parse_bibtex_to_dict


def convert_placeholders_to_citations(
    paper_content: PaperContent, references_bib: str
) -> PaperContent:
    references_bib_dict = parse_bibtex_to_dict(references_bib)

    converted_data = {}
    for field_name in PaperContent.model_fields.keys():
        content = getattr(paper_content, field_name)
        if content:
            converted_text = re.sub(
                r"\[([^\[\]]+?)\]",
                lambda match: _replace_citation(match, references_bib_dict),
                content,
            )
            converted_data[field_name] = converted_text
        else:
            converted_data[field_name] = content

    return PaperContent(**converted_data)


def _replace_citation(match, references_bib_dict: dict[str, dict[str, str]]):
    content = match.group(1)

    if "," not in content:
        if content in references_bib_dict:
            return f"\\cite{{{content}}}"
        return ""

    keys = [key.strip() for key in content.split(",")]

    valid_keys = [key for key in keys if key in references_bib_dict]
    if not valid_keys:
        return ""

    joined_keys = ",".join(valid_keys)
    return f"\\cite{{{joined_keys}}}"


if __name__ == "__main__":
    paper_content = PaperContent(
        title="title",
        abstract="abstract",
        introduction="Single [single_key], multiple [multi_key1, multi_key2], mixed [single_key, missing_key]",
        related_work="related",
        background="background",
        method="method",
        experimental_setup="setup",
        results="results",
        conclusion="conclusion",
    )

    reference_bib = """
@article{single_key,
 title = {Single Citation Test},
 author = {Test Author},
 year = {2023}
}

@article{multi_key1,
 title = {Multiple Citation Test 1},
 author = {Test Author 1},
 year = {2023}
}

@article{multi_key2,
 title = {Multiple Citation Test 2},
 author = {Test Author 2},
 year = {2023}
}"""

    result = convert_placeholders_to_citations(paper_content, reference_bib)
    print("Introduction:", result.introduction)
