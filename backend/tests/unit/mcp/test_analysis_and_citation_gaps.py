"""Two ways the paper pipeline used to lose content without saying so.

The analysis prompt once rendered nothing at all when no metrics were in
hand, leaving the analyst writing a results section with no results in
front of it; it now says so and still shows the frozen declarations. The
paper prompt marks any study whose title misses `references.bib` as "do
not cite", and told nobody, so citations vanished from the finished paper.
"""

import pytest

from airas.core.types.research_hypothesis import ResearchHypothesis
from airas.core.types.research_record import (
    Criterion,
    Hypothesis,
    Prediction,
    ResearchRecord,
    SeyvalClaim,
    SeyvalDesign,
    SeyvalRun,
    SeyvalVerifier,
    VerifierKind,
)
from airas.core.types.research_study import ResearchStudy
from airas.mcp.prompt_registry import build_generation_prompt
from airas.usecases.analysis.analyze_experiment import (
    analysis_context,
    render_analysis_prompt,
)
from airas.workflows.writers.write_subgraph.nodes.generate_note import (
    map_studies_to_bibtex,
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


def _context(metrics: dict, verdict: str | None = None) -> dict:
    record = ResearchRecord(
        hypotheses=[
            Hypothesis(
                id="h1",
                statement="Aggregate scores hide per-system failure.",
                assumptions=["lddt_pli stands for pose quality (c1)"],
                claims=[
                    SeyvalClaim(
                        verifier=SeyvalVerifier(kind=VerifierKind.SEYVAL),
                        id="c1",
                        statement="Component-wise beats aggregate on lddt_pli.",
                        rationale="r",
                        verdict=verdict,
                        criterion=Criterion(
                            metric="lddt_pli",
                            subject="proposed",
                            reference="baseline",
                            op=">=",
                            margin=0.02,
                        ),
                        prediction=Prediction(low=0.02, high=0.05, basis="pilot"),
                        designs=[
                            SeyvalDesign(
                                id="d1",
                                summary="s",
                                runs=[
                                    SeyvalRun(run_id="proposed"),
                                    SeyvalRun(run_id="baseline"),
                                ],
                            )
                        ],
                    )
                ],
            )
        ]
    )
    return analysis_context(record, metrics, set(metrics))


def test_a_study_without_run_outputs_says_so_instead_of_rendering_nothing():
    prompt = render_analysis_prompt(_context({}))

    assert "NONE PROVIDED" in prompt
    assert "Do not invent" in prompt
    assert "Observed difference: not available" in prompt
    # The frozen declarations still reach the analyst.
    assert "proposed.lddt_pli - baseline.lddt_pli >= 0.02" in prompt
    assert "[0.02, 0.05]" in prompt


def test_the_observed_difference_is_placed_against_the_prediction():
    metrics = {"proposed": {"lddt_pli": 0.70}, "baseline": {"lddt_pli": 0.60}}
    context = _context(metrics, verdict="supported")
    (claim,) = context["hypotheses"][0]["claims"]
    assert claim["observed"] == pytest.approx(0.10)
    assert claim["in_prediction"] is False
    prompt = render_analysis_prompt(context)
    assert "outside the predicted interval" in prompt
    assert "Verdict: supported" in prompt
    assert '"lddt_pli": 0.7' in prompt


def test_a_shortened_title_still_finds_its_citation_key():
    unmatched = unmatched_citation_titles(
        map_studies_to_bibtex([ResearchStudy(title="DiffDock")], BIB)
    )

    assert unmatched == []


def test_a_study_missing_from_the_bibliography_is_reported():
    studies = [ResearchStudy(title="PoseBusters"), ResearchStudy(title="DiffDock")]

    assert unmatched_citation_titles(map_studies_to_bibtex(studies, BIB)) == [
        "PoseBusters"
    ]


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


def _paper_prompt_with_literature() -> dict:
    return build_generation_prompt(
        "paper_writing",
        {
            "research_hypothesis": HYPOTHESIS.model_dump(),
            "experiment_history": {"cycles": []},
            "experiment_code": {"files": {"src/main.py": "print()"}},
            "research_study_list": [{"title": "PoseBusters"}],
            "references_bib": BIB,
            "literature": [
                {
                    "id": "s1",
                    "title": "DiffDock",
                    "bibkey": "diffdock2023",
                    "passages": [
                        {
                            "id": "s1.p1",
                            "node_type": "result",
                            "quote": "DiffDock reaches 38% top-1 success.",
                        }
                    ],
                }
            ],
        },
    )


def test_the_note_lists_each_passage_with_its_locator_syntax():
    prompt = _paper_prompt_with_literature()["prompt"]

    assert "[@diffdock2023]" in prompt
    assert 's1.p1 (result): "DiffDock reaches 38% top-1 success."' in prompt
    assert "[@citation_key, s1.p2]" in prompt


def test_literature_from_the_record_replaces_the_do_not_cite_path():
    result = _paper_prompt_with_literature()

    assert "warnings" not in result
    assert "PoseBusters" not in result["prompt"]
