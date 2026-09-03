"""Append-only guarantees against real git repositories, and `verified`.

Containment is checked over the record's git history: a rewritten claim,
a changed run condition, a verified flag going back to false all violate
it. `verified` itself is simple for now — every run under the claim has
results — and the order proof (was the claim declared before its runs
executed) is not modelled yet.
"""

import json
import subprocess
from pathlib import Path

import pytest

from airas.core.research_paths import RECORD_PATH
from airas.core.types.research_record import (
    ClaimDeclaration,
    DesignDeclaration,
    Hypothesis,
    ResearchRecord,
    RunDeclaration,
)
from airas.core.types.run_provenance import (
    PROVENANCE_MANIFEST_PATH,
    ResultsDirProvenance,
    RunProvenanceManifest,
)
from airas.infra.local_git import commit_paths
from airas.usecases.publication.paper_values.record import load_record, save_record
from airas.usecases.verification.record_history import (
    compute_claim_status,
    record_append_only_status,
)


def _git(repo: Path, *args: str) -> str:
    result = subprocess.run(
        ["git", "-C", str(repo), *args], capture_output=True, text=True, check=True
    )
    return result.stdout.strip()


def _init_repo(tmp_path: Path) -> None:
    _git(tmp_path, "init", "-q")
    _git(tmp_path, "config", "user.email", "test@example.com")
    _git(tmp_path, "config", "user.name", "test")


def _commit_all(tmp_path: Path, message: str) -> str:
    _git(tmp_path, "add", "-A")
    _git(tmp_path, "commit", "-q", "-m", message)
    return _git(tmp_path, "rev-parse", "HEAD")


def _claim(claim_id: str = "c1", run_id: str = "proposed") -> ClaimDeclaration:
    return ClaimDeclaration(
        id=claim_id,
        statement="Proposed beats baseline.",
        designs=[DesignDeclaration(id="d1", runs=[RunDeclaration(run_id=run_id)])],
    )


def _record(*claims: ClaimDeclaration) -> ResearchRecord:
    return ResearchRecord(
        hypotheses=[
            Hypothesis(
                id="h1", statement="Proposed beats baseline.", claims=list(claims)
            )
        ]
    )


def _write_results(tmp_path: Path, run_commit: str) -> RunProvenanceManifest:
    results = tmp_path / ".research" / "results" / "proposed"
    results.mkdir(parents=True)
    (results / "metrics.json").write_text(json.dumps({"accuracy": 0.9}))
    manifest = RunProvenanceManifest(
        dirs={
            "proposed": ResultsDirProvenance(
                execution_id="run-abc", commit_hash=run_commit
            )
        }
    )
    (tmp_path / PROVENANCE_MANIFEST_PATH).write_text(
        manifest.model_dump_json(indent=2) + "\n"
    )
    return manifest


def _status(record: ResearchRecord, present: set[str] | None = None):
    return compute_claim_status(record, {"proposed"} if present is None else present)


def _c1(record: ResearchRecord) -> ClaimDeclaration:
    return record.hypotheses[0].claims[0]


# --------------------------------------------------------------- committing


def test_commit_paths_commits_only_the_given_paths(tmp_path: Path) -> None:
    _init_repo(tmp_path)
    save_record(str(tmp_path), _record(_claim()))
    (tmp_path / "unrelated.txt").write_text("left uncommitted")

    sha = commit_paths(tmp_path, [RECORD_PATH], "prereg: declare")
    assert sha == _git(tmp_path, "rev-parse", "HEAD")
    assert "unrelated.txt" in _git(tmp_path, "status", "--porcelain")
    # No changes on the paths: returns the current HEAD instead of failing.
    assert commit_paths(tmp_path, [RECORD_PATH], "noop") == sha
    # Not a git repo: degrades to None.
    assert commit_paths(tmp_path / "nowhere", [RECORD_PATH], "x") is None
    # A pathspec matching nothing is fatal to git add, so callers must only
    # pass paths they actually wrote.
    (tmp_path / "touched.txt").write_text("changed")
    assert commit_paths(tmp_path, ["touched.txt", "never/written"], "x") is None
    assert "touched.txt" in _git(tmp_path, "status", "--porcelain")


# ------------------------------------------------- verified and containment


def test_a_claim_whose_runs_all_have_results_is_verified(tmp_path: Path) -> None:
    _init_repo(tmp_path)
    save_record(str(tmp_path), _record(_claim()))
    freeze = _commit_all(tmp_path, "prereg")
    _write_results(tmp_path, freeze)
    _commit_all(tmp_path, "results")

    record = load_record(str(tmp_path))
    assert [s.verified for s in _status(record)] == [True]
    assert record_append_only_status(tmp_path, record)[0] == "ok"


def test_a_claim_missing_any_result_is_not_verified() -> None:
    record = _record(_claim())
    assert _status(record, present=set())[0].verified is False
    status = _status(record, present=set())[0]
    assert status.checks[0].results_present is False


def test_a_claim_with_two_runs_needs_both(tmp_path: Path) -> None:
    claim = _claim()
    claim.designs[0].runs.append(RunDeclaration(run_id="baseline"))
    record = _record(claim)
    assert _status(record, present={"proposed"})[0].verified is False
    assert _status(record, present={"proposed", "baseline"})[0].verified is True


def test_appending_a_claim_after_results_is_allowed(tmp_path: Path) -> None:
    """Containment permits it; whether it counts as preregistered is TODO."""
    _init_repo(tmp_path)
    save_record(str(tmp_path), _record())
    freeze = _commit_all(tmp_path, "prereg without the claim")
    _write_results(tmp_path, freeze)
    _commit_all(tmp_path, "results")

    record = load_record(str(tmp_path))
    record.hypotheses[0].claims.append(_claim())
    save_record(str(tmp_path), record)
    _commit_all(tmp_path, "claim added afterwards")
    assert record_append_only_status(tmp_path, record)[0] == "ok"


def test_a_reworded_claim_violates_containment(tmp_path: Path) -> None:
    _init_repo(tmp_path)
    save_record(str(tmp_path), _record(_claim()))
    _commit_all(tmp_path, "prereg")

    record = load_record(str(tmp_path))
    _c1(record).statement = "Proposed is competitive with baseline."  # softened
    save_record(str(tmp_path), record)

    status, problems, _ = record_append_only_status(tmp_path, record)
    assert status == "violated"
    assert any("statement" in p for p in problems)


def test_changed_run_conditions_violate_containment(tmp_path: Path) -> None:
    _init_repo(tmp_path)
    save_record(str(tmp_path), _record(_claim()))
    _commit_all(tmp_path, "prereg")

    record = load_record(str(tmp_path))
    _c1(record).designs[0].runs[0].params = {"mode": "pilot"}
    status, problems, _ = record_append_only_status(tmp_path, record)
    assert status == "violated"
    assert any("params" in p for p in problems)


def test_legitimate_append_keeps_earlier_claims_verified(tmp_path: Path) -> None:
    _init_repo(tmp_path)
    save_record(str(tmp_path), _record(_claim()))
    freeze = _commit_all(tmp_path, "prereg")
    _write_results(tmp_path, freeze)
    _commit_all(tmp_path, "results")

    record = load_record(str(tmp_path))
    record.hypotheses[0].claims.append(_claim("c2", run_id="ablation"))
    save_record(str(tmp_path), record)
    _commit_all(tmp_path, "append exploratory claim")

    assert record_append_only_status(tmp_path, record)[0] == "ok"
    assert {s.id: s.verified for s in _status(record)} == {"c1": True, "c2": False}


def test_verified_true_then_false_is_a_violation(tmp_path: Path) -> None:
    _init_repo(tmp_path)
    record = _record(_claim())
    _c1(record).verified = True
    save_record(str(tmp_path), record)
    _commit_all(tmp_path, "verified")

    record = load_record(str(tmp_path))
    _c1(record).verified = False
    status, problems, _ = record_append_only_status(tmp_path, record)
    assert status == "violated"
    assert any("verified" in p for p in problems)


# ------------------------------------------------------------- degradation


def test_no_git_repo_reports_unavailable(tmp_path: Path) -> None:
    save_record(str(tmp_path), _record(_claim()))
    record = load_record(str(tmp_path))
    status, _, _ = record_append_only_status(tmp_path, record)
    assert status == "unavailable"


def test_shallow_clone_reports_unavailable(tmp_path: Path) -> None:
    origin = tmp_path / "origin"
    origin.mkdir()
    _init_repo(origin)
    save_record(str(origin), _record(_claim()))
    _commit_all(origin, "prereg")
    save_record(str(origin), _record(_claim(), _claim("c2", run_id="ablation")))
    _commit_all(origin, "append")

    clone = tmp_path / "clone"
    subprocess.run(
        ["git", "clone", "-q", "--depth", "1", origin.as_uri(), str(clone)],
        check=True,
        capture_output=True,
    )
    record = load_record(str(clone))
    status, _, _ = record_append_only_status(clone, record)
    assert status == "unavailable"


def test_unparseable_committed_record_is_a_violation(tmp_path: Path) -> None:
    _init_repo(tmp_path)
    (tmp_path / RECORD_PATH).parent.mkdir(parents=True)
    (tmp_path / RECORD_PATH).write_text("{not json")
    _commit_all(tmp_path, "mangled record")
    save_record(str(tmp_path), _record(_claim()))
    _commit_all(tmp_path, "fixed record")

    record = load_record(str(tmp_path))
    status, problems, _ = record_append_only_status(tmp_path, record)
    assert status == "violated"
    assert any("not a valid record" in p for p in problems)


@pytest.mark.parametrize(
    "legacy",
    [
        {"schema_version": 1, "prereg": {}},
        {"schema_version": 2, "hypothesis": {"statement": "H"}},
    ],
)
def test_an_earlier_layout_is_rejected_with_an_explanation(
    tmp_path: Path, legacy: dict
) -> None:
    """There is no migration: containment forbids one."""
    path = tmp_path / RECORD_PATH
    path.parent.mkdir(parents=True)
    path.write_text(json.dumps(legacy))
    with pytest.raises(ValueError, match="earlier layout"):
        load_record(str(tmp_path))
