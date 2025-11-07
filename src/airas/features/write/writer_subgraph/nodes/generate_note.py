from jinja2 import Template

from airas.types.research_session import ResearchSession
from airas.types.research_study import ResearchStudy


def generate_note(
    research_session: ResearchSession,
    research_study_list: list[ResearchStudy],
    reference_research_study_list: list[ResearchStudy],
    references_bib: str,
) -> str:
    if not (best_iter := research_session.best_iteration):
        return ""

    image_files = [
        fig
        for run in best_iter.experiment_runs or []
        for fig in getattr(run.results, "figures", []) or []
    ]

    run_results = [
        f"- **{run.run_id}** (Method: {run.method_name}, "
        f"Model: {run.model_name or 'N/A'}, Dataset: {run.dataset_name or 'N/A'})\n  "
        f"{getattr(run.results, 'metrics_data', '')}"
        for run in best_iter.experiment_runs or []
        if getattr(run.results, "metrics_data", None)
    ]

    image_files.extend(
        getattr(best_iter.experimental_analysis, "comparison_figures", []) or []
    )

    template = Template(
        """\
# Research Paper Note

## 1. Proposed Method
{{ method }}

## 2. Experimental Design
{{ experimental_design_summary }}

## 3. Individual Run Results
{% for result in run_results %}
{{ result }}
{% endfor %}

## 4. Aggregated Metrics
{{ aggregated_metrics }}

## 5. Analysis Report
{{ analysis_report }}

## 6. Figures
{% for figure in image_files %}
- {{ figure }}
{% endfor %}

## 7. Reference Papers

### Main References
{% for paper in main_references %}
**{{ paper.title }}**
{{ paper.abstract }}

{% endfor %}

### Additional References
{% for paper in additional_references %}
**{{ paper.title }}**
{{ paper.abstract }}

{% endfor %}

## 8. BibTeX References
{{ references_bib }}"""
    )

    exp_analysis = getattr(best_iter, "experimental_analysis", None)
    exp_design = getattr(best_iter, "experimental_design", None)

    return template.render(
        method=best_iter.method or "",
        experimental_design_summary=getattr(exp_design, "experiment_summary", ""),
        run_results=run_results,
        aggregated_metrics=getattr(exp_analysis, "aggregated_metrics", ""),
        analysis_report=getattr(exp_analysis, "analysis_report", ""),
        image_files=image_files,
        main_references=[
            {"title": rs.title, "abstract": rs.abstract}
            for rs in research_study_list
            if rs.abstract
        ],
        additional_references=[
            {"title": rs.title, "abstract": rs.abstract}
            for rs in reference_research_study_list
            if rs.abstract
        ],
        references_bib=references_bib,
    ).strip()
