"""claims.tex: the paper's claim list is rendered from the record.

Deterministic from (record, metrics) alone, so the freeze commit carries it
with every outcome pending, and the same function regenerates it once the
runs are in.
"""

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
from airas.usecases.publication.map_record_to_publication import render_claims_tex

SEYVAL = SeyvalVerifier(kind=VerifierKind.SEYVAL)


def _record(verdict: str | None = None) -> ResearchRecord:
    return ResearchRecord(
        hypotheses=[
            Hypothesis(
                id="h1",
                statement="Method X improves accuracy.",
                assumptions=["Accuracy on this dataset stands for the property (c1)."],
                claims=[
                    SeyvalClaim(
                        verifier=SEYVAL,
                        id="c1",
                        statement="X beats the baseline.",
                        rationale="Head-to-head on the hypothesis's own metric.",
                        verdict=verdict,
                        criterion=Criterion(
                            metric="accuracy",
                            subject="run_2",
                            reference="run_1",
                            op=">=",
                            margin=0.02,
                        ),
                        prediction=Prediction(low=0.02, high=0.04, basis="pilot"),
                        designs=[
                            SeyvalDesign(
                                id="d1",
                                runs=[
                                    SeyvalRun(run_id="run_1"),
                                    SeyvalRun(run_id="run_2"),
                                ],
                            )
                        ],
                    )
                ],
            )
        ]
    )


def test_pending_before_any_run() -> None:
    tex = render_claims_tex(_record(), {})
    assert r"\textbf{H1.} Method X improves accuracy." in tex
    assert r"\item[\textbf{C1}] X beats the baseline." in tex
    assert r"\emph{Rationale:} Head-to-head on the hypothesis's own metric." in tex
    assert r"\item Accuracy on this dataset stands for the property (c1)." in tex
    assert r"\texttt{\detokenize{run_2}}.\texttt{\detokenize{accuracy}} $-$" in tex
    assert r"$\geq 0.02$" in tex
    assert r"\emph{Prediction:} $[0.02, 0.04]$ (pilot)." in tex
    assert r"\emph{Observed:} pending." in tex
    assert r"\emph{Verdict:} pending." in tex


def test_observed_and_verdict_once_the_runs_are_in() -> None:
    metrics = {"run_1": {"accuracy": 0.871}, "run_2": {"accuracy": 0.902}}
    tex = render_claims_tex(_record("supported"), metrics)
    assert r"\emph{Observed:} 0.031." in tex
    assert r"\emph{Verdict:} supported." in tex


def test_an_unresolvable_metric_stays_pending() -> None:
    tex = render_claims_tex(_record(), {"run_1": {"f1": 0.5}, "run_2": {"f1": 0.6}})
    assert r"\emph{Observed:} pending." in tex
