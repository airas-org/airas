import json
import logging
import re
from typing import Any

from jinja2 import Template

from airas.core.types.experiment_code import ExperimentCode
from airas.core.types.experiment_history import (
    ExperimentCycleAction,
    ExperimentHistory,
)
from airas.core.types.research_hypothesis import ResearchHypothesis
from airas.core.types.research_study import ResearchStudy
from airas.usecases.publication.nodes.parse_bibtex_to_dict import parse_bibtex_to_dict

logger = logging.getLogger(__name__)

_NORMALIZE_RE = re.compile(r"[\W_]+")


def _normalize(text: str) -> str:
    if not text:
        return ""
    return _NORMALIZE_RE.sub("", text).lower()


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
    experiment_history: ExperimentHistory,
    experiment_code: ExperimentCode,
    research_study_list: list[ResearchStudy],
    references_bib: str,
) -> str:
    mapped_studies = _map_studies_to_bibtex(research_study_list, references_bib)

    # Find the final cycle (complete) for main results
    final_cycle = next(
        (
            c
            for c in reversed(experiment_history.cycles)
            if c.decision and c.decision.action == ExperimentCycleAction.COMPLETE
        ),
        None,
    )

    # Fallback to last cycle if no complete decision found
    if final_cycle is None:
        logger.warning(
            "No cycle with COMPLETE decision found, falling back to last cycle"
        )
        final_cycle = (
            experiment_history.cycles[-1] if experiment_history.cycles else None
        )

    # Collect redesign history for methodology section
    redesign_cycles = [
        cycle
        for cycle in experiment_history.cycles
        if cycle.decision and cycle.decision.action == ExperimentCycleAction.REDESIGN
    ]

    final_results = final_cycle.experimental_results if final_cycle else None
    diagram_figures = final_results.diagram_figures or [] if final_results else []
    result_figures = final_results.result_figures or [] if final_results else []

    metrics_data_json = (
        json.dumps(final_results.metrics_data, indent=2, ensure_ascii=False)
        if final_results and final_results.metrics_data
        else ""
    )

    template = Template(
        """\
# Research Paper Note

## 1. Research Hypothesis
{{ research_hypothesis }}

## 2. Experimental Design
{% if final_cycle %}{{ final_cycle.experimental_design }}{% endif %}

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
{% if final_results and final_results.stdout %}{{ final_results.stdout }}{% else %}(not available){% endif %}

### Stderr:
{% if final_results and final_results.stderr %}{{ final_results.stderr }}{% else %}(not available){% endif %}

### Metrics Data:
{% if metrics_data_json %}{{ metrics_data_json }}{% else %}(not available){% endif %}

## 6. Experimental Analysis
{% if final_cycle and final_cycle.experimental_analysis %}{{ final_cycle.experimental_analysis }}{% else %}(not available){% endif %}

{% if redesign_cycles %}
## 7. Design Iteration History
During the research process, the experimental design was revised based on preliminary findings.
Include this context in the methodology section to ensure transparency.
{% for cycle in redesign_cycles %}
### Iteration {{ loop.index }}
- Design: {{ cycle.experimental_design.experiment_summary }}
- Reason for change: {{ cycle.decision.reasoning }}
- What was changed: {{ cycle.decision.design_instruction }}
{% endfor %}
{% endif %}

## {{ '8' if redesign_cycles else '7' }}. Reference Candidates (Source Material)
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

## {{ '9' if redesign_cycles else '8' }}. Full BibTeX (For Reference)
{{ references_bib }}"""
    )

    return template.render(
        research_hypothesis=research_hypothesis,
        final_cycle=final_cycle,
        final_results=final_results,
        experiment_code=experiment_code,
        diagram_figures=diagram_figures,
        result_figures=result_figures,
        metrics_data_json=metrics_data_json,
        redesign_cycles=redesign_cycles,
        mapped_studies=mapped_studies,
        references_bib=references_bib,
    ).strip()
