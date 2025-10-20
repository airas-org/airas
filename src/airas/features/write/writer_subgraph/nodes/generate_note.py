from jinja2 import Template

from airas.types.research_hypothesis import ResearchHypothesis
from airas.types.research_study import ResearchStudy


def generate_note(
    new_method: ResearchHypothesis,
    research_study_list: list[ResearchStudy],
    reference_research_study_list: list[ResearchStudy],
    references_bib: str,
) -> str:
    all_image_files = []
    run_results = []
    for run in new_method.experiment_runs:
        if run.results.figures:
            all_image_files.extend(run.results.figures)

        if run.results.metrics_data:
            run_results.append(
                f"- **{run.run_id}** (Method: {run.method_name}, "
                f"Model: {run.model_name or 'N/A'}, "
                f"Dataset: {run.dataset_name or 'N/A'})\n  {run.results.metrics_data}"
            )
    if new_method.experimental_analysis.comparison_figures:
        all_image_files.extend(new_method.experimental_analysis.comparison_figures)

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
{{ references_bib }}""".strip()
    )

    return template.render(
        method=new_method.method,
        experimental_design_summary=new_method.experimental_design.experiment_summary,
        run_results=run_results,
        aggregated_metrics=new_method.experimental_analysis.aggregated_metrics,
        analysis_report=new_method.experimental_analysis.analysis_report,
        image_files=all_image_files,
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
