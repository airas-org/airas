"""A seyval claim's criterion: frozen at declaration, judged from the metrics.

The verdict is a pure function of the declared criterion and the runs'
metrics.
"""

import pytest
from pydantic import ValidationError

from airas.core.types.research_record import (
    Criterion,
    Hypothesis,
    LeanClaim,
    LeanDesign,
    LeanParams,
    LeanRun,
    LeanVerifier,
    Prediction,
    ResearchRecord,
    SeyvalClaim,
    SeyvalDesign,
    SeyvalResult,
    SeyvalRun,
    SeyvalVerifier,
    VerifierKind,
)
from airas.research_record.read.derive_results import compute_claim_statuses
from airas.research_record.verify._verify_record_git_history import (
    _containment_violations,
)
from airas.research_record.verify._verify_record_in_itself import (
    verify_record_in_itself as verify_consistency,
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


def test_a_criterion_subject_must_be_the_claims_own_run() -> None:
    record = _record(_criterion(reference="ghost"), {})
    assert any("'ghost'" in p for p in verify_consistency(record))
    # both runs are the claim's own, in either role
    assert (
        verify_consistency(
            _record(_criterion(subject="baseline", reference="proposed"), {})
        )
        == []
    )
    assert verify_consistency(_record(_criterion(), {})) == []


def _two_claims(shared_result: dict[str, object] | None) -> ResearchRecord:
    """c1 owns i20 and i80; c2 owns i40 and compares it against c1's i80."""

    def run(run_id: str, metrics: dict[str, object] | None) -> SeyvalRun:
        results = [SeyvalResult(id=run_id, metrics=metrics)] if metrics else []
        return SeyvalRun(run_id=run_id, results=results)

    def claim(cid: str, criterion: Criterion, runs: list[SeyvalRun]) -> SeyvalClaim:
        return SeyvalClaim(
            verifier=SEYVAL,
            id=cid,
            statement=f"{cid} holds.",
            rationale="Budget comparison.",
            criterion=criterion,
            prediction=PREDICTION,
            designs=[SeyvalDesign(id="d1", runs=runs)],
        )

    return ResearchRecord(
        hypotheses=[
            Hypothesis(
                id="h1",
                statement="More budget helps, then saturates.",
                claims=[
                    claim(
                        "c1",
                        _criterion(subject="i80", reference="i20"),
                        [run("i20", {"accuracy": 0.7}), run("i80", shared_result)],
                    ),
                    claim(
                        "c2",
                        _criterion(
                            subject="i40", reference="i80", op="<=", margin=0.05
                        ),
                        [run("i40", {"accuracy": 0.88})],
                    ),
                ],
            )
        ]
    )


def test_a_criterion_reference_must_be_a_seyval_run() -> None:
    # A Lean run carries no metrics, so "the same metric" can never hold.
    lean = LeanClaim(
        id="c2",
        statement="The lemma holds.",
        rationale="Formal counterpart.",
        verifier=LeanVerifier(kind=VerifierKind.LEAN),
        designs=[
            LeanDesign(
                id="d1",
                runs=[
                    LeanRun(
                        run_id="lemma",
                        params=LeanParams(module="Airas.L", decl="l", statement="x"),
                    )
                ],
            )
        ],
    )
    record = _record(_criterion(reference="lemma"), {})
    record.hypotheses[0].claims.append(lean)
    assert any("'lemma'" in p and "seyval" in p for p in verify_consistency(record))


def test_a_criterion_may_reference_another_claims_run() -> None:
    # Declaring is fine: i80 is a run of the record, just not of c2.
    assert verify_consistency(_two_claims({"accuracy": 0.9})) == []
    # c2 is not verified until c1's i80 has its result, then it is judged on it.
    pending = compute_claim_statuses(_two_claims(None), {"i20", "i40"})
    assert [(s.id, s.verified, s.verdict) for s in pending] == [
        ("c1", False, None),
        ("c2", False, None),
    ]
    done = compute_claim_statuses(_two_claims({"accuracy": 0.9}), {"i20", "i40", "i80"})
    assert [(s.id, s.verified, s.verdict) for s in done] == [
        ("c1", True, "supported"),  # 0.9 - 0.7 >= 0
        ("c2", True, "supported"),  # 0.88 - 0.9 = -0.02 <= 0.05
    ]


# -------------------------------------------------------------- containment


def test_the_criterion_is_frozen_with_the_claim() -> None:
    older, newer = _record(_criterion(), {}), _record(_criterion(margin=0.01), {})
    assert any(
        "criterion" in p
        for p in _containment_violations(older.model_dump(), newer.model_dump())
    )
