from jinja2 import Template

from airas.types.research_hypothesis import ResearchHypothesis
from airas.types.research_study import ResearchStudy


def generate_note(
    new_method: ResearchHypothesis,
    research_study_list: list[ResearchStudy],
    reference_research_study_list: list[ResearchStudy],
    references_bib: str,
) -> str:
    template = Template(
        """\
## Method
{{ method }}

## Experimental Details
{{ experimental_details}}

## Experiment Code
{{ experiment_code }}

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
        experimental_details=new_method.experimental_design.experiment_details,
        experimental_results=new_method.experimental_results.result,
        analysis=new_method.experimental_analysis.analysis_report,
        image_file_name_list=new_method.experimental_results.image_file_name_list,
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
