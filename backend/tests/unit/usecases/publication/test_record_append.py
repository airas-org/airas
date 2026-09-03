import pytest
from pydantic import ValidationError

from airas.core.types.paper_values import ValueDeclaration
from airas.core.types.research_record import (
    ClaimDeclaration,
    PreregSection,
    RunDeclaration,
)
from airas.usecases.publication.paper_values.record import (
    active,
    prereg_append_violations,
    prereg_consistency_problems,
)


def _prereg() -> PreregSection:
    return PreregSection(
        hypothesis="H.",
        design="D.",
        runs=[RunDeclaration(run_id="proposed"), RunDeclaration(run_id="baseline")],
        claims=[
            ClaimDeclaration(
                id="c1",
                statement="Proposed beats baseline.",
                criterion="gain > 0",
                predicted_interval="2-4 points (pilot)",
                run_ids=["proposed", "baseline"],
                value_keys=["gain"],
            )
        ],
        values=[
            ValueDeclaration(
                key="gain",
                op="pct_improve",
                refs=["proposed.accuracy", "baseline.accuracy"],
            )
        ],
    )


def test_pure_append_is_allowed() -> None:
    older = _prereg()
    newer = _prereg()
    newer.runs.append(RunDeclaration(run_id="ablation"))
    newer.claims.append(
        ClaimDeclaration(
            id="c2",
            statement="Ablation holds.",
            criterion="x > 0",
            predicted_interval="1-2 (pilot)",
            run_ids=["ablation"],
        )
    )
    newer.notes.append("exploratory extension")
    assert prereg_append_violations(older, newer) == []


def test_rewritten_claim_is_a_violation() -> None:
    older = _prereg()
    newer = _prereg()
    newer.claims[0].criterion = "gain > -5"  # weakened after the fact
    assert prereg_append_violations(older, newer) == ["claims entry 'c1' was modified"]


def test_removed_entry_is_a_violation() -> None:
    older = _prereg()
    newer = _prereg()
    newer.claims.clear()
    assert any("removed" in p for p in prereg_append_violations(older, newer))


def test_rewritten_hypothesis_is_a_violation() -> None:
    older = _prereg()
    newer = _prereg()
    newer.hypothesis = "A better-sounding H."
    assert "hypothesis was rewritten" in prereg_append_violations(older, newer)


def test_edited_note_is_a_violation() -> None:
    older = _prereg()
    older.notes.append("as observed")
    newer = _prereg()
    newer.notes.append("as predicted")
    assert any("notes" in p for p in prereg_append_violations(older, newer))


def test_supersede_keeps_old_entry_and_deactivates_it() -> None:
    prereg = _prereg()
    prereg.claims.append(
        ClaimDeclaration(
            id="c2",
            statement="Refined claim.",
            criterion="gain > 1",
            predicted_interval="2-3 (pilot)",
            run_ids=["proposed", "baseline"],
            supersedes="c1",
        )
    )
    assert prereg_consistency_problems(prereg) == []
    assert [c.id for c in active(prereg.claims, "id")] == ["c2"]
    # The superseded original is still in the record, untouched.
    assert prereg.claims[0].id == "c1"


def test_consistency_rejects_duplicate_ids() -> None:
    prereg = _prereg()
    prereg.claims.append(prereg.claims[0].model_copy())
    assert any("duplicate 'c1'" in p for p in prereg_consistency_problems(prereg))


def test_consistency_rejects_unknown_supersede_target() -> None:
    prereg = _prereg()
    prereg.values.append(
        ValueDeclaration(key="gain2", refs=["proposed.accuracy"], supersedes="ghost")
    )
    assert any("unknown 'ghost'" in p for p in prereg_consistency_problems(prereg))


def test_consistency_rejects_claim_with_undeclared_run() -> None:
    prereg = _prereg()
    prereg.claims[0].run_ids.append("undeclared-run")
    assert any(
        "run 'undeclared-run' is not declared" in p
        for p in prereg_consistency_problems(prereg)
    )


def test_consistency_rejects_claim_with_undeclared_value_key() -> None:
    prereg = _prereg()
    prereg.claims[0].value_keys.append("ghost_key")
    assert any(
        "value key 'ghost_key' is not declared" in p
        for p in prereg_consistency_problems(prereg)
    )


def test_claim_id_pattern_is_enforced() -> None:
    with pytest.raises(ValidationError):
        ClaimDeclaration(
            id="claim-one",
            statement="s",
            criterion="c",
            predicted_interval="i",
            run_ids=["proposed"],
        )
