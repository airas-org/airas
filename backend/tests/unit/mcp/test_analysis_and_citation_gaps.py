"""Two ways the paper pipeline used to lose content without saying so.

The analysis prompt rendered nothing at all when `experimental_results`
carried no `metrics_data` — the outer `if` was true, so it did not even
fall through to "No experimental results available yet", and the analyst
was left writing a results section with no results in front of it. The
paper prompt marks any study whose title misses `references.bib` as "do
not cite", and told nobody, so citations vanished from the finished paper.
"""

from airas.core.types.research_hypothesis import ResearchHypothesis
from airas.core.types.research_study import ResearchStudy
from airas.mcp.prompt_registry import build_generation_prompt
from airas.usecases.writers.write_subgraph.nodes.generate_note import (
    unmatched_citation_titles,
)

HYPOTHESIS = ResearchHypothesis(
    open_problems="Aggregation hides per-system failure.",
    method="Report the components separately.",
    experimental_setup="150 systems.",
    primary_metric="lddt_pli",
    supporting_metrics=["pb_valid"],
    expected_result="The aggregate and the components disagree.",
    expected_conclusion="Aggregate scores are not sufficient.",
)

DESIGN = {
    "proposed_method": {
        "method_name": "Component-wise reporting",
        "description": "Report lDDT-PLI, PB-valid and coverage separately.",
    }
}

BIB = """
@article{diffdock2023,
  title  = {DiffDock: Diffusion Steps, Twists, and Turns for Molecular Docking},
  author = {Corso, Gabriele},
  year   = {2023}
}
"""


def _analysis_prompt(experimental_results: dict) -> str:
    return build_generation_prompt(
        "experiment_analysis",
        {
            "research_hypothesis": HYPOTHESIS.model_dump(),
            "experimental_design": DESIGN,
            "experiment_code": {"files": {"src/main.py": "print()"}},
            "experimental_results": experimental_results,
        },
    )["prompt"]


def test_results_without_metrics_data_say_so_instead_of_rendering_nothing():
    prompt = _analysis_prompt({"stdout": "lddt_pli mean 0.648"})

    assert "NONE PROVIDED" in prompt
    assert "Do not invent" in prompt
    # Whatever *was* passed still has to reach the analyst.
    assert "lddt_pli mean 0.648" in prompt


def test_metrics_data_is_rendered_when_present():
    prompt = _analysis_prompt({"metrics_data": {"run-1": {"lddt_pli": 0.648}}})

    assert "0.648" in prompt
    assert "NONE PROVIDED" not in prompt


def test_expected_result_reaches_the_prompt_that_asks_about_it():
    prompt = _analysis_prompt({"metrics_data": {"run-1": {}}})

    # Instruction 4 asks whether the results match the hypothesis; without
    # the expectation there is nothing to compare them against.
    assert "consistent with the research hypothesis" in prompt
    assert "The aggregate and the components disagree." in prompt


def test_a_shortened_title_still_finds_its_citation_key():
    unmatched = unmatched_citation_titles([ResearchStudy(title="DiffDock")], BIB)

    assert unmatched == []


def test_a_study_missing_from_the_bibliography_is_reported():
    studies = [ResearchStudy(title="PoseBusters"), ResearchStudy(title="DiffDock")]

    assert unmatched_citation_titles(studies, BIB) == ["PoseBusters"]


def test_the_paper_prompt_warns_about_studies_it_will_not_cite():
    result = build_generation_prompt(
        "paper_writing",
        {
            "research_hypothesis": HYPOTHESIS.model_dump(),
            "experiment_history": {"cycles": []},
            "experiment_code": {"files": {"src/main.py": "print()"}},
            "research_study_list": [{"title": "PoseBusters"}],
            "references_bib": BIB,
        },
    )

    assert "Do not cite" in result["prompt"]
    assert "PoseBusters" in result["warnings"][0]


def test_no_warning_when_every_study_is_citable():
    result = build_generation_prompt(
        "paper_writing",
        {
            "research_hypothesis": HYPOTHESIS.model_dump(),
            "experiment_history": {"cycles": []},
            "experiment_code": {"files": {"src/main.py": "print()"}},
            "research_study_list": [{"title": "DiffDock"}],
            "references_bib": BIB,
        },
    )

    assert "warnings" not in result
