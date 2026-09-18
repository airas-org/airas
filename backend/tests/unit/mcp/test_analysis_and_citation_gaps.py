"""Two ways the paper pipeline used to lose content without saying so.

The analysis prompt once rendered nothing at all when no metrics were in
hand, leaving the analyst writing a results section with no results in
front of it; it now says so and still shows the frozen declarations. The
legacy paper writer marks any study whose title misses `references.bib`
as "do not cite" — the matching has to find shortened titles.
"""

import pytest

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
from airas.usecases.analysis.analyze_experiment import (
    analysis_context,
    render_analysis_prompt,
)
from airas.workflows.writers.write_subgraph.nodes.generate_note import (
    map_studies_to_bibtex,
    unmatched_citation_titles,
)

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
