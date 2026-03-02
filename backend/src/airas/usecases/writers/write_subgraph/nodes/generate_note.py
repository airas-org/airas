import re
from typing import Any

from jinja2 import Template

from airas.core.types.experiment_code import ExperimentCode
from airas.core.types.experimental_analysis import ExperimentalAnalysis
from airas.core.types.experimental_design import ExperimentalDesign
from airas.core.types.experimental_results import ExperimentalResults
from airas.core.types.research_hypothesis import ResearchHypothesis
from airas.core.types.research_study import ResearchStudy
from airas.usecases.publication.nodes.parse_bibtex_to_dict import parse_bibtex_to_dict


def _normalize(text: str) -> str:
    if not text:
        return ""
    return re.sub(r"[\W_]+", "", text).lower()


def _map_studies_to_bibtex(
    research_study_list: list[ResearchStudy], references_bib: str
) -> list[dict[str, Any]]:
    parsed_references = parse_bibtex_to_dict(references_bib)

    # { normalized_title: citation_key }
    bib_map = {
        _normalize(entry.get("title", "")): entry.get("ID")
        for entry in parsed_references.values()
        if entry.get("title") and entry.get("ID")
    }

    return [
        {
            "title": study.title,
            "citation_key": bib_map.get(_normalize(study.title)),
            "content": study.llm_extracted_info,
        }
        for study in research_study_list
    ]


def generate_note(
    research_hypothesis: ResearchHypothesis,
    experimental_design: ExperimentalDesign,
    experiment_code: ExperimentCode,
    experimental_results: ExperimentalResults,
    experimental_analysis: ExperimentalAnalysis,
    research_study_list: list[ResearchStudy],
    references_bib: str,
) -> str:
    mapped_studies = _map_studies_to_bibtex(research_study_list, references_bib)

    all_figures = experimental_results.figures or []
    diagram_figures = [f for f in all_figures if "diagrams" in f]
    result_figures = [f for f in all_figures if "diagrams" not in f]

    template = Template(
        """\
# Research Paper Note

## 1. Research Hypothesis
{{ research_hypothesis }}

## 2. Experimental Design
{{ experimental_design }}

## 3. Method Diagrams
The following diagram files illustrate the proposed method architecture and should be placed in the **Method section** of the paper.
{% if diagram_figures %}
Figures:
{% for f in diagram_figures %}
- {{ f }}
{% endfor %}
{% else %}
No method diagrams available.
{% endif %}

## 4. Experiment Code
{{ experiment_code }}

## 5. Experimental Results
### Result Figures (place in the Results section of the paper):
{% if result_figures %}
{% for f in result_figures %}
- {{ f }}
{% endfor %}
{% else %}
No result figures available.
{% endif %}

### Stdout:
{{ experimental_results.stdout }}

### Stderr:
{{ experimental_results.stderr }}

### Metrics Data:
{{ experimental_results.metrics_data }}

## 6. Experimental Analysis
{{ experimental_analysis }}

## 7. Reference Candidates (Source Material)
This section lists papers available for citation.
**Instructions for Writer:**
- The **Citation Key** (e.g., `[@vaswani-2017-attention]`) matches the entry in the BibTeX references.
- Select and use the appropriate Citation Key when citing these works in the text.
- You do NOT need to cite all papers listed here. Only cite papers that are relevant to your research.

{% for paper in mapped_studies %}
### {{ paper.title }}
{% if paper.citation_key %}
**Citation Key:** [@{{ paper.citation_key }}]
{% else %}
*(No Citation Key - Do not cite)*
{% endif %}

**Summary:**
{{ paper.content }}

---
{% endfor %}

## 8. Full BibTeX (For Reference)
{{ references_bib }}"""
    )

    return template.render(
        research_hypothesis=research_hypothesis,
        experimental_design=experimental_design,
        experiment_code=experiment_code,
        experimental_results=experimental_results,
        experimental_analysis=experimental_analysis,
        diagram_figures=diagram_figures,
        result_figures=result_figures,
        mapped_studies=mapped_studies,
        references_bib=references_bib,
    ).strip()
