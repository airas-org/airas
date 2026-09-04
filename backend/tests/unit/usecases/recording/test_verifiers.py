"""Verifiers other than seyval: the same tree, typed leaves, reports read into the record."""

from __future__ import annotations

import asyncio
import json
import subprocess
from pathlib import Path
from typing import Any

import pytest
from pydantic import ValidationError

from airas.core.research_paths import RESULTS_DIR
from airas.core.types.research_record import (
    ClaimDeclaration,
    Hypothesis,
    LeanClaim,
    LeanResult,
    LlmJudgeClaim,
    LlmJudgeResult,
    ResearchRecord,
)
from airas.usecases.recording.update_or_load_record import (
    save_record,
    update_record_with_results,
)
from airas.usecases.recording.verify_record import (
    RecordVerification,
    _containment_violations,
    verify_record,
)


def record_append_violations(older: ResearchRecord, newer: ResearchRecord) -> list[str]:
    return _containment_violations(older.model_dump(), newer.model_dump())


LEAN_REPORT = {
    "commit": "a" * 40,
    "toolchain": "leanprover/lean4:v4.12.0",
    "mathlib_rev": "b" * 40,
    "statement": "∀ (n : Nat), n + 0 = n",
    "axioms": ["propext"],
    "errors": [],
}


def _verify(path: str) -> RecordVerification:
    return asyncio.run(
        verify_record(path, check_provenance=False, require_history=False)
    )


def _git(repo: Path, *args: str) -> str:
    return subprocess.run(
        ["git", "-C", str(repo), *args], capture_output=True, text=True, check=True
    ).stdout.strip()


def _init(repo: Path) -> None:
    _git(repo, "init", "-q")
    _git(repo, "config", "user.email", "test@example.com")
    _git(repo, "config", "user.name", "test")


def _commit(repo: Path, message: str) -> str:
    _git(repo, "add", "-A")
    _git(repo, "commit", "-q", "-m", message)
    return _git(repo, "rev-parse", "HEAD")


def _record(claim: ClaimDeclaration) -> ResearchRecord:
    return ResearchRecord(
        hypotheses=[Hypothesis(id="h1", statement="It holds.", claims=[claim])]
    )


def _lean_claim() -> LeanClaim:
    return LeanClaim.model_validate(
        {
            "id": "c1",
            "statement": "Zero is a right identity.",
            "verifier": {"kind": "lean", "toolchain": "leanprover/lean4:v4.12.0"},
            "designs": [
                {
                    "id": "d1",
                    "runs": [
                        {
                            "run_id": "thm1",
                            "params": {
                                "module": "Airas.Thm1",
                                "decl": "thm1",
                                "statement": "∀ (n : Nat),  n + 0 = n",
                            },
                        }
                    ],
                }
            ],
        }
    )


def _judge_claim() -> LlmJudgeClaim:
    return LlmJudgeClaim.model_validate(
        {
            "id": "c1",
            "statement": "Participants preferred the new interface.",
            "verifier": {
                "kind": "llm_judge",
                "model": "openai/gpt-x-20260101",
                "rubric": "rubric.md",
                "samples": 3,
            },
            "designs": [
                {
                    "id": "d1",
                    "runs": [
                        {
                            "run_id": "interviews",
                            "params": {"evidence": ["evidence.md"]},
                        }
                    ],
                }
            ],
        }
    )


def _write(repo: Path, run_id: str, name: str, payload: Any) -> Path:
    out = repo / RESULTS_DIR / run_id
    out.mkdir(parents=True, exist_ok=True)
    path = out / name
    path.write_text(json.dumps(payload, ensure_ascii=False))
    return path


def _c1(record: ResearchRecord) -> ClaimDeclaration:
    return record.hypotheses[0].claims[0]


def _realize(repo: Path, record: ResearchRecord) -> ResearchRecord:
    update_record_with_results(repo, record, {}, None)
    save_record(str(repo), record)
    _commit(repo, "realize")
    return record


def _lean_repo(tmp_path: Path, report: dict[str, Any] = LEAN_REPORT) -> ResearchRecord:
    _init(tmp_path)
    record = _record(_lean_claim())
    save_record(str(tmp_path), record)
    _commit(tmp_path, "prereg")
    _write(tmp_path, "thm1", "lean.json", report)
    _commit(tmp_path, "check")
    return _realize(tmp_path, record)


def _judge_repo(tmp_path: Path, verdict: str = "supported") -> ResearchRecord:
    _init(tmp_path)
    (tmp_path / "rubric.md").write_text("Supported if most participants say so.\n")
    (tmp_path / "evidence.md").write_text("P1: better. P2: better. P3: worse.\n")
    record = _record(_judge_claim())
    save_record(str(tmp_path), record)
    _commit(tmp_path, "prereg")
    _write(
        tmp_path,
        "interviews",
        "judgment.json",
        {
            "id": "resp-1",
            "commit": "a" * 40,
            "model_returned": "gpt-x-20260101",
            "inputs_sha256": "f" * 64,
            "verdict": verdict,
            "votes": {verdict: 2, "inconclusive": 1},
            "recorded_at": "2026-09-04T00:00:00+00:00",
        },
    )
    _write(
        tmp_path,
        "interviews",
        "rationale.json",
        [{"verdict": verdict, "rationale": "..."}],
    )
    _commit(tmp_path, "judge")
    return _realize(tmp_path, record)


# ------------------------------------------------------------ the schema


def test_a_lean_run_must_declare_its_statement() -> None:
    raw = _lean_claim().model_dump()
    del raw["designs"][0]["runs"][0]["params"]["statement"]
    with pytest.raises(ValidationError, match="statement"):
        LeanClaim.model_validate(raw)


def test_a_verdict_may_be_set_once_and_never_changed() -> None:
    before = _record(_lean_claim())
    after = _record(_lean_claim())
    _c1(after).verdict = "supported"
    assert record_append_violations(before, after) == []
    changed = _record(_lean_claim())
    _c1(changed).verdict = "refuted"
    assert any("verdict" in p for p in record_append_violations(after, changed))


# ------------------------------------------------------------ lean


def test_a_sorry_free_build_supports_the_claim(tmp_path: Path) -> None:
    record = _lean_repo(tmp_path)
    claim = _c1(record)
    result = claim.designs[0].runs[0].results[0]
    assert isinstance(result, LeanResult)
    assert result.errors == [] and result.statement == LEAN_REPORT["statement"]
    assert claim.verified and claim.verdict == "supported"
    report = _verify(str(tmp_path))
    assert report.ok, report.problems
    assert report.stage == "results"


@pytest.mark.parametrize(
    ("change", "error"),
    [
        ({"axioms": ["propext", "sorryAx"]}, "sorry"),
        ({"statement": "∀ (n : Nat), n = n"}, "statement differs"),
        ({"axioms": ["myAxiom"]}, "outside allowed_axioms"),
        (
            {"statement": "", "errors": ["error: unknown identifier 'thm1'"]},
            "unknown identifier",
        ),
    ],
)
def test_a_sorry_a_drifted_statement_a_foreign_axiom_or_a_failed_build_is_inconclusive(
    tmp_path: Path, change: dict[str, Any], error: str
) -> None:
    record = _lean_repo(tmp_path, {**LEAN_REPORT, **change})
    claim = _c1(record)
    assert claim.verified and claim.verdict == "inconclusive"
    assert any(error in e for e in claim.designs[0].runs[0].results[0].errors)
    assert _verify(str(tmp_path)).ok


def test_a_tampered_lean_report_fails(tmp_path: Path) -> None:
    _lean_repo(tmp_path, {**LEAN_REPORT, "axioms": ["sorryAx"]})
    _write(tmp_path, "thm1", "lean.json", LEAN_REPORT)
    report = _verify(str(tmp_path))
    assert not report.ok
    assert any("differs from the lean report" in m for m in report.problems)


def test_a_verdict_written_by_hand_before_any_run_fails(tmp_path: Path) -> None:
    _init(tmp_path)
    record = _record(_lean_claim())
    _c1(record).verdict = "supported"
    save_record(str(tmp_path), record)
    _commit(tmp_path, "prereg")
    report = _verify(str(tmp_path))
    assert report.stage == "prereg" and not report.ok


# ------------------------------------------------------------ llm_judge


def test_a_judgment_is_read_into_the_record(tmp_path: Path) -> None:
    record = _judge_repo(tmp_path)
    claim = _c1(record)
    assert claim.verified and claim.verdict == "supported"
    result = claim.designs[0].runs[0].results[0]
    assert isinstance(result, LlmJudgeResult)
    assert result.warnings == ["votes split {'supported': 2, 'inconclusive': 1}"]
    assert _verify(str(tmp_path)).ok
