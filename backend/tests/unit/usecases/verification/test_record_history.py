"""Order and append-only guarantees, against real git repositories.

The scenarios mirror the integrity contract: a claim declared before its
run verifies; a claim declared after the run's results never does; a
rewritten claim both violates append-only and loses its verification.
"""

import json
import subprocess
from pathlib import Path

from airas.core.research_paths import RECORD_PATH
from airas.core.types.paper_record import (
    ClaimDeclaration,
    PaperRecord,
    PreregSection,
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


def _claim(claim_id: str = "c1", criterion: str = "gain > 0") -> ClaimDeclaration:
    return ClaimDeclaration(
        id=claim_id,
        statement="Proposed beats baseline.",
        criterion=criterion,
        predicted_interval="2-4 points (pilot)",
        run_ids=["proposed"],
    )


def _record(*claims: ClaimDeclaration) -> PaperRecord:
    return PaperRecord(
        prereg=PreregSection(
            hypothesis="H.",
            design="D.",
            runs=[RunDeclaration(run_id="proposed")],
            claims=list(claims),
        )
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


def test_claim_declared_before_run_is_verified(tmp_path: Path) -> None:
    _init_repo(tmp_path)
    save_record(str(tmp_path), _record(_claim()))
    freeze = _commit_all(tmp_path, "prereg")
    manifest = _write_results(tmp_path, freeze)  # the run executed the freeze commit
    _commit_all(tmp_path, "results")

    record = load_record(str(tmp_path))
    statuses = compute_claim_status(tmp_path, record, manifest, {"proposed"})
    assert [s.verified for s in statuses] == [True]
    assert record_append_only_status(tmp_path, record)[0] == "ok"


def test_claim_appended_after_results_stays_unverified(tmp_path: Path) -> None:
    _init_repo(tmp_path)
    save_record(str(tmp_path), _record())
    freeze = _commit_all(tmp_path, "prereg without the claim")
    manifest = _write_results(tmp_path, freeze)
    _commit_all(tmp_path, "results")

    record = load_record(str(tmp_path))
    record.prereg.claims.append(_claim())  # post-hoc claim
    save_record(str(tmp_path), record)
    _commit_all(tmp_path, "sneak the claim in afterwards")

    statuses = compute_claim_status(tmp_path, record, manifest, {"proposed"})
    assert statuses[0].verified is False
    assert statuses[0].checks[0].declared_at_run_commit is False
    # Appending is legitimate — history is still append-only.
    assert record_append_only_status(tmp_path, record)[0] == "ok"


def test_rewritten_claim_violates_append_only_and_loses_verification(
    tmp_path: Path,
) -> None:
    _init_repo(tmp_path)
    save_record(str(tmp_path), _record(_claim()))
    freeze = _commit_all(tmp_path, "prereg")
    manifest = _write_results(tmp_path, freeze)
    _commit_all(tmp_path, "results")

    record = load_record(str(tmp_path))
    record.prereg.claims[0].criterion = "gain > -5"  # weakened to fit the data
    save_record(str(tmp_path), record)

    status, problems, _ = record_append_only_status(tmp_path, record)
    assert status == "violated"
    assert any("'c1' was modified" in p for p in problems)
    statuses = compute_claim_status(tmp_path, record, manifest, {"proposed"})
    assert statuses[0].verified is False


def test_legitimate_append_keeps_earlier_claims_verified(tmp_path: Path) -> None:
    _init_repo(tmp_path)
    save_record(str(tmp_path), _record(_claim()))
    freeze = _commit_all(tmp_path, "prereg")
    manifest = _write_results(tmp_path, freeze)
    _commit_all(tmp_path, "results")

    record = load_record(str(tmp_path))
    record.prereg.runs.append(RunDeclaration(run_id="ablation"))
    record.prereg.claims.append(
        ClaimDeclaration(
            id="c2",
            statement="Ablation holds.",
            criterion="x > 0",
            predicted_interval="1-2 (pilot)",
            run_ids=["ablation"],
        )
    )
    save_record(str(tmp_path), record)
    _commit_all(tmp_path, "append exploratory claim")

    assert record_append_only_status(tmp_path, record)[0] == "ok"
    statuses = {
        s.id: s.verified
        for s in compute_claim_status(tmp_path, record, manifest, {"proposed"})
    }
    assert statuses == {"c1": True, "c2": False}


def test_run_commit_outside_history_is_not_verified(tmp_path: Path) -> None:
    _init_repo(tmp_path)
    save_record(str(tmp_path), _record(_claim()))
    _commit_all(tmp_path, "prereg")
    manifest = _write_results(tmp_path, "deadbeef" * 5)
    _commit_all(tmp_path, "results with foreign commit")

    record = load_record(str(tmp_path))
    statuses = compute_claim_status(tmp_path, record, manifest, {"proposed"})
    assert statuses[0].verified is False
    assert statuses[0].checks[0].commit_in_history is False


def test_no_git_repo_reports_unavailable(tmp_path: Path) -> None:
    save_record(str(tmp_path), _record(_claim()))
    record = load_record(str(tmp_path))
    status, _, _ = record_append_only_status(tmp_path, record)
    assert status == "unavailable"
    statuses = compute_claim_status(tmp_path, record, None, {"proposed"})
    assert statuses[0].verified is False


def test_shallow_clone_reports_unavailable(tmp_path: Path) -> None:
    origin = tmp_path / "origin"
    origin.mkdir()
    _init_repo(origin)
    save_record(str(origin), _record(_claim()))
    _commit_all(origin, "prereg")
    save_record(str(origin), _record(_claim(), _claim("c2", "x > 0")))
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
