import re
from typing import Any

import bibtexparser
from jinja2 import Template

from airas.types.experiment_code import ExperimentCode
from airas.types.experimental_analysis import ExperimentalAnalysis
from airas.types.experimental_design import ExperimentalDesign
from airas.types.experimental_results import ExperimentalResults
from airas.types.research_hypothesis import ResearchHypothesis
from airas.types.research_study import ResearchStudy


def _normalize(text: str) -> str:
    if not text:
        return ""
    return re.sub(r"[\W_]+", "", text).lower()


def _map_studies_to_bibtex(
    research_study_list: list[ResearchStudy], references_bib: str
) -> list[dict[str, Any]]:
    bib = bibtexparser.loads(references_bib)

    # { normalized_title: citation_key }
    bib_map = {
        _normalize(entry.get("title", "")): entry.get("ID")
        for entry in bib.entries
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

    template = Template(
        """\
# Research Paper Note

## 1. Research Hypothesis
{{ research_hypothesis }}

## 2. Experimental Design
{{ experimental_design }}

## 3. Experiment Code
{{ experiment_code }}

## 4. Experimental Results
{{ experimental_results }}

## 5. Experimental Analysis
{{ experimental_analysis }}

## 6. Reference Candidates (Source Material)
This section lists papers available for citation.
**Instructions for Writer:**
- The **Citation Key** (e.g., `[@vaswani2017]`) matches the entry in the BibTeX references.
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

## 7. Full BibTeX (For Reference)
{{ references_bib }}"""
    )

    return template.render(
        research_hypothesis=research_hypothesis,
        experimental_design=experimental_design,
        experiment_code=experiment_code,
        experimental_results=experimental_results,
        experimental_analysis=experimental_analysis,
        mapped_studies=mapped_studies,
        references_bib=references_bib,
    ).strip()
