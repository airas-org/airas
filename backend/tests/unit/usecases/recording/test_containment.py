"""Containment: a newer record must contain its predecessor whole.

One rule replaces the per-field append-only checks an earlier record
needed. The tests are written against the behaviours that rule is supposed
to guarantee — a claim cannot be reworded after results exist, a result
cannot be dropped, a list cannot be reordered — rather than against the
individual messages, so the rule can be reimplemented without rewriting
them. The one sanctioned change, `verified` going from false to true, is
covered in both directions.
"""

import pytest

from airas.core.types.map_record_to_publication import (
    TableColumnSpec,
    TableRowSpec,
    TableSpec,
)
from airas.core.types.research_record import (
    ClaimDeclaration,
    Hypothesis,
    ResearchRecord,
    SeyvalClaim,
    SeyvalDesign,
    SeyvalResult,
    SeyvalRun,
    SeyvalVerifier,
    VerifierKind,
    active,
)
from airas.usecases.recording.verify_record import (
    _containment_violations,
    _verify_consistency,
)

SEYVAL = SeyvalVerifier(kind=VerifierKind.SEYVAL)


def record_append_violations(older: ResearchRecord, newer: ResearchRecord) -> list[str]:
    return _containment_violations(older.model_dump(), newer.model_dump())


def _record() -> ResearchRecord:
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
                        designs=[
                            SeyvalDesign(
                                id="d1",
                                summary="Head-to-head on one dataset.",
                                runs=[
                                    SeyvalRun(
                                        run_id="proposed", params={"mode": "full"}
                                    ),
                                    SeyvalRun(run_id="baseline"),
                                ],
                            )
                        ],
                    )
                ],
            )
        ]
    )


def _claim(claim_id: str = "c2", run_id: str = "ablation") -> ClaimDeclaration:
    return SeyvalClaim(
        verifier=SEYVAL,
        id=claim_id,
        statement="The ablation holds.",
        designs=[SeyvalDesign(id="d1", runs=[SeyvalRun(run_id=run_id)])],
    )


def _c1(record: ResearchRecord) -> ClaimDeclaration:
    return record.hypotheses[0].claims[0]


# ------------------------------------------------------------- what may grow


def test_appending_claims_hypotheses_and_notes_is_allowed() -> None:
    older, newer = _record(), _record()
    newer.hypotheses[0].claims.append(_claim())
    newer.hypotheses[0].notes.append("exploratory extension")
    newer.hypotheses.append(Hypothesis(id="h2", statement="A second hypothesis."))
    assert record_append_violations(older, newer) == []


def test_results_may_be_appended_to_a_frozen_declaration() -> None:
    """The freeze is on the declaration, not on the record file."""
    older, newer = _record(), _record()
    _c1(newer).designs[0].runs[0].results.append(
        SeyvalResult(
            verifier="seyval", id="e1", commit="c" * 40, metrics={"accuracy": 0.9}
        )
    )
    assert record_append_violations(older, newer) == []


def test_verified_may_go_from_false_to_true() -> None:
    """The one value the procedure changes after writing it."""
    older, newer = _record(), _record()
    _c1(newer).verified = True
    assert record_append_violations(older, newer) == []


# -------------------------------------------------------- what may not change


def test_verified_may_not_go_back_to_false() -> None:
    older, newer = _record(), _record()
    _c1(older).verified = True
    assert record_append_violations(older, newer) == [
        "hypotheses[0].claims[0].verified: changed (True -> False)"
    ]


def test_rewording_a_claim_after_the_fact_is_a_violation() -> None:
    older, newer = _record(), _record()
    _c1(newer).statement = "Proposed is not worse than baseline."
    assert any("statement" in p for p in record_append_violations(older, newer))


def test_changing_a_runs_declared_conditions_is_a_violation() -> None:
    older, newer = _record(), _record()
    _c1(newer).designs[0].runs[0].params = {"mode": "pilot"}
    assert any("params" in p for p in record_append_violations(older, newer))


def test_rewriting_the_hypothesis_is_a_violation() -> None:
    older, newer = _record(), _record()
    newer.hypotheses[0].statement = "A better-sounding hypothesis."
    assert any("statement" in p for p in record_append_violations(older, newer))


def test_dropping_a_recorded_result_is_a_violation() -> None:
    """Deleting the run that came out badly is the failure mode this stops."""
    older, newer = _record(), _record()
    _c1(older).designs[0].runs[0].results.append(
        SeyvalResult(verifier="seyval", id="e1", metrics={"accuracy": 0.9})
    )
    assert any("removed" in p for p in record_append_violations(older, newer))


def test_reordering_a_list_is_a_violation() -> None:
    """Append order is what makes 'last entry wins' safe to rely on."""
    older, newer = _record(), _record()
    _c1(newer).designs[0].runs.reverse()
    assert record_append_violations(older, newer) != []


def test_containment_reports_the_path_to_the_change() -> None:
    problems = _containment_violations(
        {"a": {"b": [1, 2]}, "keep": 1}, {"a": {"b": [1, 9]}, "keep": 1}
    )
    assert problems == ["a.b[1]: changed (2 -> 9)"]


def test_containment_allows_new_keys() -> None:
    assert _containment_violations({"a": 1}, {"a": 1, "b": 2}) == []


# ---------------------------------------------------------- last entry wins


def test_the_last_entry_for_an_id_is_the_live_one() -> None:
    """Adding a design to an existing claim is a revision of the claim."""
    record = _record()
    revised = _c1(record).model_copy(deep=True)
    revised.designs.append(SeyvalDesign(id="d2", runs=[SeyvalRun(run_id="ablation")]))
    record.hypotheses[0].claims.append(revised)

    live = [c for _, c in record.active_claims()]
    assert [c.id for c in live] == ["c1"]
    assert [d.id for d in live[0].designs] == ["d1", "d2"]
    assert set(record.run_index()) == {"proposed", "baseline", "ablation"}


# ---------------------------------------------- consistency at freeze time


def test_a_run_declared_under_two_claims_is_caught() -> None:
    """Run ids address a results directory, so a run belongs to one claim."""
    record = _record()
    record.hypotheses[0].claims.append(_claim("c2", run_id="proposed"))
    assert any("repo-unique" in p for p in _verify_consistency(record))


def test_a_claim_with_no_run_is_caught() -> None:
    """A claim with no experiment cannot be verified."""
    record = _record()
    record.hypotheses[0].claims.append(
        SeyvalClaim(verifier=SEYVAL, id="c2", statement="Untestable as declared.")
    )
    assert any("declares no run" in p for p in _verify_consistency(record))


def test_a_table_row_on_an_undeclared_run_is_caught() -> None:
    record = _record()
    record.hypotheses[0].tables.append(
        TableSpec(
            key="main",
            caption="Results.",
            columns=[TableColumnSpec(header="Acc", ref_path="accuracy")],
            rows=[TableRowSpec(run_id="ghost", label="?")],
        )
    )
    assert any("which no design declares" in p for p in _verify_consistency(record))


def test_a_clean_record_has_no_problems() -> None:
    assert _verify_consistency(_record()) == []


@pytest.mark.parametrize("bad_id", ["claim1", "C1", "c0"])
def test_ids_follow_their_pattern(bad_id: str) -> None:
    with pytest.raises(ValueError):
        SeyvalClaim(verifier=SEYVAL, id=bad_id, statement="x")


def test_active_keeps_order_and_takes_the_last_entry_per_id() -> None:
    runs = [
        SeyvalRun(run_id="a"),
        SeyvalRun(run_id="b"),
        SeyvalRun(run_id="a", description="revised"),
    ]
    assert [(r.run_id, r.description) for r in active(runs, "run_id")] == [
        ("a", "revised"),
        ("b", ""),
    ]
