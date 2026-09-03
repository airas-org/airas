"""Order and append-only guarantees, against real git repositories.

The scenarios mirror the integrity contract: a claim declared before its run
verifies; a claim declared after the run's results never does; a rewritten
claim both violates containment and loses its verification. `verified` and
`criterion_met` are checked separately, because a properly preregistered
claim that missed its threshold is a negative result, not a broken record.
"""

import json
import subprocess
from pathlib import Path

from airas.core.research_paths import RECORD_PATH
from airas.core.types.research_record import (
    Bound,
    ClaimDeclaration,
    DesignDeclaration,
    Hypothesis,
    ResearchRecord,
    RunDeclaration,
    Target,
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
    design_rollup,
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


def _claim(claim_id: str = "c1", floor: float = 0.0) -> ClaimDeclaration:
    return ClaimDeclaration(
        id=claim_id,
        statement="Proposed beats baseline.",
        target=Target(op="value", refs=["proposed.accuracy"]),
        criterion=Bound(min=floor),
        predicted_interval=Bound(min=0.8, max=0.95),
        rationale="0.8-0.95, from the pilot",
    )


def _record(*claims: ClaimDeclaration, run_ids: tuple[str, ...] = ("proposed",)):
    return ResearchRecord(
        hypothesis=Hypothesis(
            statement="Proposed beats baseline.",
            claims=list(claims),
            designs=[
                DesignDeclaration(
                    id="d1",
                    summary="Head-to-head.",
                    runs=[RunDeclaration(run_id=r) for r in run_ids],
                )
            ],
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


def _status(tmp_path: Path, record, manifest, value: float | None = None):
    values: dict[str, tuple[float, str, dict[str, str]]] | None = (
        {"c1": (value, f"{value}", {})} if value is not None else None
    )
    return compute_claim_status(tmp_path, record, manifest, {"proposed"}, values)


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


# ---------------------------------------------------------- the order proof


def test_claim_declared_before_run_is_verified(tmp_path: Path) -> None:
    _init_repo(tmp_path)
    save_record(str(tmp_path), _record(_claim()))
    freeze = _commit_all(tmp_path, "prereg")
    manifest = _write_results(tmp_path, freeze)  # the run executed the freeze commit
    _commit_all(tmp_path, "results")

    record = load_record(str(tmp_path))
    statuses = _status(tmp_path, record, manifest)
    assert [s.verified for s in statuses] == [True]
    assert record_append_only_status(tmp_path, record)[0] == "ok"


def test_claim_appended_after_results_stays_unverified(tmp_path: Path) -> None:
    _init_repo(tmp_path)
    save_record(str(tmp_path), _record())
    freeze = _commit_all(tmp_path, "prereg without the claim")
    manifest = _write_results(tmp_path, freeze)
    _commit_all(tmp_path, "results")

    record = load_record(str(tmp_path))
    record.hypothesis.claims.append(_claim())  # post-hoc claim
    save_record(str(tmp_path), record)
    _commit_all(tmp_path, "sneak the claim in afterwards")

    statuses = _status(tmp_path, record, manifest)
    assert statuses[0].verified is False
    assert statuses[0].checks[0].declared_at_run_commit is False
    # Appending is legitimate — history is still append-only.
    assert record_append_only_status(tmp_path, record)[0] == "ok"


def test_rewritten_claim_violates_containment_and_loses_verification(
    tmp_path: Path,
) -> None:
    _init_repo(tmp_path)
    save_record(str(tmp_path), _record(_claim()))
    freeze = _commit_all(tmp_path, "prereg")
    manifest = _write_results(tmp_path, freeze)
    _commit_all(tmp_path, "results")

    record = load_record(str(tmp_path))
    record.hypothesis.claims[0].criterion = Bound(min=-5.0)  # weakened to fit
    save_record(str(tmp_path), record)

    status, problems, _ = record_append_only_status(tmp_path, record)
    assert status == "violated"
    assert any("criterion.min" in p for p in problems)
    assert _status(tmp_path, record, manifest)[0].verified is False


def test_rewritten_run_declaration_loses_verification(tmp_path: Path) -> None:
    """The run's declared conditions are frozen alongside the claim."""
    _init_repo(tmp_path)
    save_record(str(tmp_path), _record(_claim()))
    freeze = _commit_all(tmp_path, "prereg")
    manifest = _write_results(tmp_path, freeze)
    _commit_all(tmp_path, "results")

    record = load_record(str(tmp_path))
    record.hypothesis.designs[0].runs[0].overrides = {"mode": "pilot"}
    statuses = _status(tmp_path, record, manifest)
    assert statuses[0].verified is False
    assert "did not exist at the run commit" in (statuses[0].checks[0].detail or "")


def test_legitimate_append_keeps_earlier_claims_verified(tmp_path: Path) -> None:
    _init_repo(tmp_path)
    save_record(str(tmp_path), _record(_claim()))
    freeze = _commit_all(tmp_path, "prereg")
    manifest = _write_results(tmp_path, freeze)
    _commit_all(tmp_path, "results")

    record = load_record(str(tmp_path))
    record.hypothesis.designs[0].runs.append(RunDeclaration(run_id="ablation"))
    record.hypothesis.claims.append(
        ClaimDeclaration(
            id="c2",
            statement="The ablation holds.",
            target=Target(op="value", refs=["ablation.accuracy"]),
            criterion=Bound(min=0.0),
            predicted_interval=Bound(min=0.1, max=0.2),
            rationale="0.1-0.2, from the pilot",
        )
    )
    save_record(str(tmp_path), record)
    _commit_all(tmp_path, "append exploratory claim")

    assert record_append_only_status(tmp_path, record)[0] == "ok"
    statuses = {s.id: s.verified for s in _status(tmp_path, record, manifest)}
    assert statuses == {"c1": True, "c2": False}


def test_run_commit_outside_history_is_not_verified(tmp_path: Path) -> None:
    _init_repo(tmp_path)
    save_record(str(tmp_path), _record(_claim()))
    _commit_all(tmp_path, "prereg")
    manifest = _write_results(tmp_path, "deadbeef" * 5)
    _commit_all(tmp_path, "results with foreign commit")

    record = load_record(str(tmp_path))
    statuses = _status(tmp_path, record, manifest)
    assert statuses[0].verified is False
    assert statuses[0].checks[0].commit_in_history is False


# ----------------------------------------- verified is not the same as met


def test_a_verified_claim_can_miss_its_criterion(tmp_path: Path) -> None:
    """A negative result: preregistered and executed properly, threshold missed."""
    _init_repo(tmp_path)
    save_record(str(tmp_path), _record(_claim(floor=0.95)))
    freeze = _commit_all(tmp_path, "prereg")
    manifest = _write_results(tmp_path, freeze)
    _commit_all(tmp_path, "results")

    record = load_record(str(tmp_path))
    status = _status(tmp_path, record, manifest, value=0.9)[0]
    assert status.verified is True
    assert status.criterion_met is False


def test_an_unverified_claim_that_met_its_criterion_is_still_unverified(
    tmp_path: Path,
) -> None:
    """Hitting the number does not substitute for having declared it first."""
    _init_repo(tmp_path)
    save_record(str(tmp_path), _record())
    freeze = _commit_all(tmp_path, "prereg without the claim")
    manifest = _write_results(tmp_path, freeze)
    _commit_all(tmp_path, "results")

    record = load_record(str(tmp_path))
    record.hypothesis.claims.append(_claim())
    status = _status(tmp_path, record, manifest, value=0.9)[0]
    assert status.criterion_met is True
    assert status.verified is False


def test_criterion_is_unknown_until_a_value_exists(tmp_path: Path) -> None:
    _init_repo(tmp_path)
    save_record(str(tmp_path), _record(_claim()))
    freeze = _commit_all(tmp_path, "prereg")
    manifest = _write_results(tmp_path, freeze)
    _commit_all(tmp_path, "results")

    record = load_record(str(tmp_path))
    assert _status(tmp_path, record, manifest)[0].criterion_met is None


# ------------------------------------------------------------- degradation


def test_no_git_repo_reports_unavailable(tmp_path: Path) -> None:
    save_record(str(tmp_path), _record(_claim()))
    record = load_record(str(tmp_path))
    status, _, _ = record_append_only_status(tmp_path, record)
    assert status == "unavailable"
    assert _status(tmp_path, record, None)[0].verified is False


def test_shallow_clone_reports_unavailable(tmp_path: Path) -> None:
    origin = tmp_path / "origin"
    origin.mkdir()
    _init_repo(origin)
    save_record(str(origin), _record(_claim()))
    _commit_all(origin, "prereg")
    save_record(str(origin), _record(_claim(), _claim("c2")))
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


def test_a_v1_record_is_rejected_with_an_explanation(tmp_path: Path) -> None:
    """The old prereg/results layout has no automatic migration."""
    path = tmp_path / RECORD_PATH
    path.parent.mkdir(parents=True)
    path.write_text(json.dumps({"schema_version": 1, "prereg": {}}))
    try:
        load_record(str(tmp_path))
    except ValueError as e:
        assert "schema_version 1" in str(e)
    else:
        raise AssertionError("a v1 record should not load")


# ---------------------------------------------------------------- rollup


def test_design_rollup_counts_executed_runs(tmp_path: Path) -> None:
    record = _record(_claim(), run_ids=("proposed", "baseline"))
    assert design_rollup(record) == {"d1": {"runs": 2, "executed": 0}}
