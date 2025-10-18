from jinja2 import Template

from airas.types.research_hypothesis import ResearchHypothesis
from airas.types.research_study import ResearchStudy


def generate_note(
    new_method: ResearchHypothesis,
    research_study_list: list[ResearchStudy],
    reference_research_study_list: list[ResearchStudy],
    references_bib: str,
) -> str:
    # Extract selected experiments
    selected_experiments = []
    if new_method.experimental_design and new_method.experimental_design.experiments:
        selected_experiments = [
            exp
            for exp in new_method.experimental_design.experiments
            if exp.evaluation and exp.evaluation.is_selected_for_paper
        ]

    # Combine results and images from all selected experiments
    combined_results = []
    all_image_files = []
    for exp in selected_experiments:
        if exp.results:
            combined_results.append(f"**{exp.experiment_id}**: {exp.results.result}")
            if exp.results.image_file_name_list:
                all_image_files.extend(exp.results.image_file_name_list)

    template = Template(
        """\
## Method
{{ method }}

## Experimental Strategy
{{ experimental_strategy }}

## Experimental Results
{{ experimental_results }}

## Analysis
{{ analysis }}

## Image Files
{{ image_file_name_list | join("\n") }}

## Reference Papers
{{ research_study_list | join("\n") }}
{{ reference_research_study_list | join("\n") }}

## BibTeX References
{{ references_bib }}""".strip()
    )

    return template.render(
        method=new_method.method,
        experimental_strategy=new_method.experimental_design.experiment_strategy
        if new_method.experimental_design
        else "",
        experimental_results="\n\n".join(combined_results) if combined_results else "",
        analysis=new_method.experimental_analysis.analysis_report
        if new_method.experimental_analysis
        else "",
        image_file_name_list=all_image_files,
        research_study_list=[
            f"{research_study.title}\n{research_study.abstract}"
            for research_study in research_study_list
            if research_study.abstract
        ],
        reference_research_study_list=[
            f"{reference_research_study.title}\n{reference_research_study.abstract}"
            for reference_research_study in reference_research_study_list
            if reference_research_study.abstract
        ],
        references_bib=references_bib,
    ).strip()
