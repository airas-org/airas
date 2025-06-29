import re
from logging import getLogger

from jinja2 import Environment

from airas.services.api_client.llm_client.llm_facade_client import (
    LLM_MODEL,
    LLMFacadeClient,
)
from airas.types.paper import PaperContent

logger = getLogger(__name__)


def _replace_underscores_in_keys(paper_dict: dict[str, str]) -> dict[str, str]:
    return {key.replace("_", " "): value for key, value in paper_dict.items()}


def _replace_placeholders(
    latex_text: str,
    references_bib: dict[str, str],  # {"[[CITATION_1]]": "@article{smith2023, ... }"}
) -> str:
    for placeholder, bibtex_entry in references_bib.items():
        match = re.match(r"@\w+\{([^,]+),", bibtex_entry)
        if not match:
            logger.warning(
                f"Could not extract citation key from BibTeX entry: {bibtex_entry}"
            )
            continue
        entry_key = match.group(1)
        citation = f"\\citep{{{entry_key}}}"
        latex_text = latex_text.replace(placeholder, citation)
    return latex_text


def convert_to_latex(
    llm_name: LLM_MODEL,
    prompt_template: str,
    paper_content_with_placeholders: dict[str, str],
    references_bib: dict[str, str],
    figures_dir: str = "images",
    client: LLMFacadeClient | None = None,
) -> dict[str, str]:
    client = client or LLMFacadeClient(llm_name)

    data = {
        "figures_dir": figures_dir,
        "sections": [
            {"name": section, "content": paper_content_with_placeholders[section]}
            for section in paper_content_with_placeholders.keys()
        ],
        "citation_placeholders": list(references_bib.keys()),
    }

    env = Environment()
    template = env.from_string(prompt_template)
    messages = template.render(data)

    output, cost = client.structured_outputs(
        message=messages,
        data_model=PaperContent,
    )
    if output is None:
        raise ValueError("Error: No response from the model in convert_to_latex.")

    missing_fields = [
        field
        for field in PaperContent.model_fields
        if field not in output or not output[field].strip()
    ]
    if missing_fields:
        raise ValueError(f"Missing or empty fields in model response: {missing_fields}")

    output = _replace_underscores_in_keys(output)
    output = {
        section: _replace_placeholders(content, references_bib)
        for section, content in output.items()
    }

    return output


if __name__ == "__main__":
    from airas.publication.latex_subgraph.prompt.convert_to_latex_prompt import (
        convert_to_latex_prompt,
    )

    llm_name = "o3-mini-2025-01-31"
    paper_content_with_placeholders = {
        "Title": "Sample Title",
        "Abstract": "This is a sample abstract.",
        "Introduction": "This is a sample introduction including a citation [[CITATION_1]].",
        "Related Work": "This is a sample related work",
        "Background": "Sample background section.",
        "Method": "Sample method description.",
        "Experimental Setup": "Sample experimental setup.",
        "Results": "Sample results.",
        "Conclusions": "Sample conclusion.",
    }
    references_bib = {
        "[[CITATION_1]]": "@article{Boyd2005, author = {Stephen Boyd and V. Balakrishnan and {\\'E}ric F\\'eron and Laurent El Ghaoui}, title = {History of linear matrix inequalities in control theory}, year = {2005}, volume = {1}, pages = {31--34}, doi = {10.1109/acc.1994.751687} }\n"
    }
    result = convert_to_latex(
        llm_name=llm_name,
        prompt_template=convert_to_latex_prompt,
        references_bib=references_bib,
        paper_content_with_placeholders=paper_content_with_placeholders,
    )
    print(f"result: {result}")
