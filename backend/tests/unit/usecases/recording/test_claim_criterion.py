"""A seyval claim's criterion: frozen at declaration, judged from the metrics.

The verdict is a pure function of the declared criterion and the runs'
metrics.
"""

import pytest
from pydantic import ValidationError

from airas.core.types.research_record import (
    Criterion,
    Hypothesis,
    Prediction,
    ResearchRecord,
    SeyvalClaim,
    SeyvalDesign,
    SeyvalResult,
    SeyvalRun,
    SeyvalVerifier,
    VerifierKind,
)
from airas.usecases.recording.update_or_load_record import compute_claim_statuses
from airas.usecases.recording.verify_record import (
    _containment_violations,
    _verify_consistency,
)

SEYVAL = SeyvalVerifier(kind=VerifierKind.SEYVAL)
PREDICTION = Prediction(low=0.02, high=0.04, basis="pilot")


def _criterion(**kw: object) -> Criterion:
    base = dict(metric="accuracy", subject="proposed", reference="baseline", op=">=")
    return Criterion(**{**base, **kw})


def _record(
    criterion: Criterion,
    proposed: dict[str, object],
    baseline: dict[str, object] | None = None,
) -> ResearchRecord:
    def run(run_id: str, metrics: dict[str, object] | None) -> SeyvalRun:
        results = [SeyvalResult(id=run_id, metrics=metrics)] if metrics else []
        return SeyvalRun(run_id=run_id, results=results)

    return ResearchRecord(
        hypotheses=[
            Hypothesis(
                id="h1",
                statement="Proposed beats baseline.",
                claims=[
                    SeyvalClaim(
                        verifier=SEYVAL,
                        id="c1",
                        statement="Proposed beats baseline on accuracy.",
                        rationale="Head-to-head on the hypothesis's own metric.",
                        criterion=criterion,
                        prediction=PREDICTION,
                        designs=[
                            SeyvalDesign(
                                id="d1",
                                runs=[
                                    run("proposed", proposed),
                                    run("baseline", baseline),
                                ],
                            )
                        ],
                    )
                ],
            )
        ]
    )


def _verdict(record: ResearchRecord) -> str | None:
    return compute_claim_statuses(record, {"proposed", "baseline"})[0].verdict


# ------------------------------------------------------------------ verdict


@pytest.mark.parametrize(
    ("criterion", "proposed", "baseline", "verdict"),
    [
        (
            _criterion(margin=0.02),
            {"accuracy": 0.902},
            {"accuracy": 0.871},
            "supported",
        ),
        (_criterion(margin=0.05), {"accuracy": 0.902}, {"accuracy": 0.871}, "refuted"),
        # exactly at the margin counts as met, float error notwithstanding
        (_criterion(margin=0.03), {"accuracy": 0.93}, {"accuracy": 0.90}, "supported"),
        (
            _criterion(op=">", margin=0.03),
            {"accuracy": 0.93},
            {"accuracy": 0.90},
            "refuted",
        ),
        (
            _criterion(reference=0.9),
            {"accuracy": 0.902},
            {"accuracy": 0.5},
            "supported",
        ),
        # a loss: lower by at least 0.1
        (
            _criterion(metric="loss.final", op="<=", margin=-0.1),
            {"loss": {"final": 0.2}},
            {"loss": {"final": 0.35}},
            "supported",
        ),
        (_criterion(), {"f1": 0.9}, {"accuracy": 0.871}, "inconclusive"),
        (_criterion(), {"accuracy": "n/a"}, {"accuracy": 0.871}, "inconclusive"),
    ],
)
def test_the_verdict_follows_the_criterion(criterion, proposed, baseline, verdict):
    assert _verdict(_record(criterion, proposed, baseline)) == verdict


def test_no_verdict_until_every_run_has_a_result() -> None:
    assert _verdict(_record(_criterion(), {"accuracy": 0.9}, None)) is None


# -------------------------------------------------------------- declaration


def test_a_criterion_must_be_a_range_apart_from_itself() -> None:
    with pytest.raises(ValidationError, match="to itself"):
        _criterion(reference="proposed")
    with pytest.raises(ValidationError, match="low < high"):
        Prediction(low=0.03, high=0.03, basis="pilot")


def test_a_criterion_may_only_name_the_claims_own_runs() -> None:
    record = _record(_criterion(reference="ghost"), {})
    assert any("'ghost'" in p for p in _verify_consistency(record))
    assert _verify_consistency(_record(_criterion(), {})) == []


# -------------------------------------------------------------- containment


def test_the_criterion_is_frozen_with_the_claim() -> None:
    older, newer = _record(_criterion(), {}), _record(_criterion(margin=0.01), {})
    assert any(
        "criterion" in p
        for p in _containment_violations(older.model_dump(), newer.model_dump())
    )
