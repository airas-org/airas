"""Containment: a newer record must contain its predecessor whole.

One rule replaces the per-field append-only checks the v1 record needed.
The tests are written against the behaviours that rule is supposed to
guarantee — a criterion cannot be weakened after results exist, an execution
cannot be dropped, a list cannot be reordered — rather than against the
individual messages, so the rule can be reimplemented without rewriting them.
"""

import pytest

from airas.core.types.research_record import (
    Bound,
    ClaimDeclaration,
    ClaimEvaluation,
    DesignDeclaration,
    Execution,
    Hypothesis,
    ResearchRecord,
    RunDeclaration,
    Target,
)
from airas.usecases.publication.paper_values.record import (
    active,
    containment_violations,
    orphan_runs,
    record_append_violations,
    record_consistency_problems,
    run_index,
)


def _record() -> ResearchRecord:
    return ResearchRecord(
        hypothesis=Hypothesis(
            statement="Proposed beats baseline.",
            claims=[
                ClaimDeclaration(
                    id="c1",
                    statement="Proposed beats baseline on accuracy.",
                    target=Target(
                        op="pct_improve",
                        refs=["proposed.accuracy", "baseline.accuracy"],
                    ),
                    criterion=Bound(min=0.0),
                    predicted_interval=Bound(min=2.0, max=4.0),
                    rationale="2-4 points, from the pilot",
                )
            ],
            designs=[
                DesignDeclaration(
                    id="d1",
                    summary="Head-to-head on one dataset.",
                    runs=[
                        RunDeclaration(run_id="proposed"),
                        RunDeclaration(run_id="baseline"),
                    ],
                )
            ],
        )
    )


def _claim(claim_id: str = "c2") -> ClaimDeclaration:
    return ClaimDeclaration(
        id=claim_id,
        statement="The ablation holds.",
        target=Target(op="value", refs=["ablation.accuracy"]),
        criterion=Bound(min=0.5),
        predicted_interval=Bound(min=0.5, max=0.7),
        rationale="within the pilot's range",
    )


# ------------------------------------------------------------- what may grow


def test_appending_claims_designs_and_notes_is_allowed() -> None:
    older, newer = _record(), _record()
    newer.hypothesis.designs[0].runs.append(RunDeclaration(run_id="ablation"))
    newer.hypothesis.claims.append(_claim())
    newer.notes.append("exploratory extension")
    assert record_append_violations(older, newer) == []


def test_results_may_be_appended_to_a_frozen_declaration() -> None:
    """The freeze is on the declaration, not on the record file."""
    older, newer = _record(), _record()
    newer.hypothesis.designs[0].runs[0].executions.append(
        Execution(execution_id="e1", commit="c" * 40, metrics={"accuracy": 0.9})
    )
    newer.hypothesis.claims[0].evaluations.append(
        ClaimEvaluation(value=3.6, display="3.6", verified=True, criterion_met=True)
    )
    assert record_append_violations(older, newer) == []


# -------------------------------------------------------- what may not change


def test_weakening_a_criterion_after_the_fact_is_a_violation() -> None:
    older, newer = _record(), _record()
    newer.hypothesis.claims[0].criterion = Bound(min=-5.0)
    assert record_append_violations(older, newer) == [
        "hypothesis.claims[0].criterion.min: changed (0.0 -> -5.0)"
    ]


def test_rewriting_the_hypothesis_is_a_violation() -> None:
    older, newer = _record(), _record()
    newer.hypothesis.statement = "A better-sounding hypothesis."
    assert any("statement" in p for p in record_append_violations(older, newer))


def test_dropping_a_recorded_execution_is_a_violation() -> None:
    """Deleting the run that came out badly is the failure mode this stops."""
    older, newer = _record(), _record()
    older.hypothesis.designs[0].runs[0].executions.append(
        Execution(execution_id="e1", metrics={"accuracy": 0.9})
    )
    assert any("removed" in p for p in record_append_violations(older, newer))


def test_reordering_a_list_is_a_violation() -> None:
    """Append order is what makes 'last entry wins' safe to rely on."""
    older, newer = _record(), _record()
    newer.hypothesis.designs[0].runs.reverse()
    assert record_append_violations(older, newer) != []


def test_a_withdrawn_entry_stays_in_the_record() -> None:
    older, newer = _record(), _record()
    newer.hypothesis.claims[0].withdrawn = True
    # Retiring a claim is an edit to the entry, so it is appended instead.
    assert record_append_violations(older, newer) != []

    appended = _record()
    retired = appended.hypothesis.claims[0].model_copy(update={"withdrawn": True})
    appended.hypothesis.claims.append(retired)
    assert record_append_violations(_record(), appended) == []
    assert [c.id for c in active(appended.hypothesis.claims, "id")] == []


def test_containment_reports_the_path_to_the_change() -> None:
    problems = containment_violations(
        {"a": {"b": [1, 2]}, "keep": 1}, {"a": {"b": [1, 9]}, "keep": 1}
    )
    assert problems == ["a.b[1]: changed (2 -> 9)"]


def test_containment_allows_new_keys() -> None:
    assert containment_violations({"a": 1}, {"a": 1, "b": 2}) == []


# ---------------------------------------------------------- last entry wins


def test_the_last_entry_for_an_id_is_the_live_one() -> None:
    record = _record()
    revised = record.hypothesis.claims[0].model_copy(
        update={"criterion": Bound(min=1.0)}
    )
    record.hypothesis.claims.append(revised)
    live = active(record.hypothesis.claims, "id")
    assert [c.id for c in live] == ["c1"]
    assert live[0].criterion.min == 1.0


# ---------------------------------------------- consistency at freeze time


def test_a_claim_referencing_an_undeclared_run_is_caught() -> None:
    record = _record()
    record.hypothesis.claims[0].target.refs = [
        "nonexistent.accuracy",
        "baseline.accuracy",
    ]
    assert record_consistency_problems(record) == [
        "claim c1: target references run 'nonexistent', which no design declares"
    ]


def test_a_run_declared_in_two_designs_is_caught() -> None:
    """Run ids address a results directory, so they must be repo-unique."""
    record = _record()
    record.hypothesis.designs.append(
        DesignDeclaration(
            id="d2", summary="Second design.", runs=[RunDeclaration(run_id="proposed")]
        )
    )
    assert any("repo-unique" in p for p in record_consistency_problems(record))


def test_duplicate_design_ids_are_caught() -> None:
    record = _record()
    record.hypothesis.designs.append(
        DesignDeclaration(id="d1", summary="Same id again.")
    )
    assert "designs: duplicate id 'd1'" in record_consistency_problems(record)


@pytest.mark.parametrize("op", ["diff", "pct_improve"])
def test_a_two_ref_op_given_one_ref_is_caught(op: str) -> None:
    record = _record()
    record.hypothesis.claims[0].target = Target(op=op, refs=["proposed.accuracy"])
    assert any("exactly 2 refs" in p for p in record_consistency_problems(record))


def test_an_unbounded_criterion_is_caught() -> None:
    """A criterion with no bound cannot refute anything."""
    record = _record()
    record.hypothesis.claims[0].criterion = Bound()
    assert "claim c1: criterion is unbounded" in record_consistency_problems(record)


def test_a_clean_record_has_no_problems() -> None:
    assert record_consistency_problems(_record()) == []


def test_runs_no_claim_references_are_listed() -> None:
    record = _record()
    record.hypothesis.designs[0].runs.append(RunDeclaration(run_id="scratch"))
    assert orphan_runs(record) == ["scratch"]
    assert set(run_index(record)) == {"proposed", "baseline", "scratch"}
