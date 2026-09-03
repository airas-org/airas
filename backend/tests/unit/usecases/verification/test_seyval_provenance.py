import json
import subprocess
from pathlib import Path
from typing import Any, cast

from airas.core.types.run_provenance import PROVENANCE_MANIFEST_PATH
from airas.infra.seyval_client import SeyvalClient
from airas.usecases.publication.paper_values.verify import (
    apply_provenance_result,
    verify_paper_record,
)
from airas.usecases.verification.seyval_provenance import SeyvalProvenanceVerifier

GIT_URL = "https://github.com/test-org/test-repo"
METRICS = {"accuracy": 0.871}
DECLARED_RUN = "run-A"


def _git(repo: Path, *args: str) -> str:
    result = subprocess.run(
        ["git", "-C", str(repo), *args], capture_output=True, text=True, check=True
    )
    return result.stdout.strip()


def _make_repo(
    tmp_path: Path, declared_run: str | None = DECLARED_RUN
) -> tuple[Path, bytes, str]:
    metrics_path = tmp_path / ".research" / "results" / "run-1" / "metrics.json"
    metrics_path.parent.mkdir(parents=True)
    metrics_bytes = json.dumps(METRICS).encode()
    metrics_path.write_bytes(metrics_bytes)

    if declared_run is not None:
        manifest_path = tmp_path / PROVENANCE_MANIFEST_PATH
        manifest_path.write_text(
            json.dumps({"dirs": {"run-1": {"execution_id": declared_run}}})
        )

    _git(tmp_path, "init", "-q")
    _git(tmp_path, "config", "user.email", "test@example.com")
    _git(tmp_path, "config", "user.name", "test")
    _git(tmp_path, "remote", "add", "origin", GIT_URL + ".git")
    _git(tmp_path, "add", "-A")
    _git(tmp_path, "commit", "-q", "-m", "results")
    commit_hash = _git(tmp_path, "rev-parse", "HEAD")
    return metrics_path, metrics_bytes, commit_hash


class FakeSeyvalClient:
    """Per-run stored outputs, so pinning to the declared run is testable."""

    def __init__(
        self,
        runs: list[dict[str, Any]],
        stored: dict[str, bytes],
        extra_outputs: dict[str, bytes] | None = None,
    ) -> None:
        self.runs = runs
        self.stored = stored  # run_id -> bytes of run-1's metrics.json
        # repo path -> bytes, for the other files a run produced
        self.extra_outputs = extra_outputs or {}

    async def alist_repositories(self) -> list[dict[str, Any]]:
        return [{"id": "repo-1", "git_url": GIT_URL + ".git"}]

    async def alist_runs(self, repository_id: str) -> list[dict[str, Any]]:
        assert repository_id == "repo-1"
        return self.runs

    async def aget_run_outputs(self, run_id: str) -> dict[str, Any]:
        outputs = [
            {
                "path": ".research/results/run-1/metrics.json",
                "download_url": f"https://example.test/{run_id}",
            }
        ]
        outputs += [
            {"path": path, "download_url": f"https://example.test/extra/{path}"}
            for path in self.extra_outputs
        ]
        return {"outputs": outputs}

    async def adownload(self, url: str) -> bytes:
        marker = "https://example.test/extra/"
        if url.startswith(marker):
            return self.extra_outputs[url[len(marker) :]]
        return self.stored[url.rsplit("/", 1)[-1]]


def _completed(run_id: str, commit_hash: str) -> dict[str, Any]:
    return {"run_id": run_id, "status": "completed", "commit_hash": commit_hash}


def _verifier(fake: FakeSeyvalClient) -> SeyvalProvenanceVerifier:
    return SeyvalProvenanceVerifier(cast(SeyvalClient, fake))


async def test_verified_when_declared_run_backs_the_bytes(tmp_path: Path) -> None:
    _, metrics_bytes, commit_hash = _make_repo(tmp_path)
    fake = FakeSeyvalClient(
        runs=[
            _completed(DECLARED_RUN, commit_hash),
            {"run_id": "run-B", "status": "failed", "commit_hash": commit_hash},
        ],
        stored={DECLARED_RUN: metrics_bytes},
    )
    result = await _verifier(fake).verify(str(tmp_path), {"run-1"})
    assert result.status == "verified"
    assert result.checks[0].run_id == DECLARED_RUN
    assert result.checks[0].commit_in_history is True
    assert result.checks[0].sibling_run_ids == []


async def test_mismatch_when_manifest_commit_disagrees_with_seyval(
    tmp_path: Path,
) -> None:
    # A manifest pointing at a later commit could make a post-hoc claim look
    # declared-before-run; the cross-check against Seyval's record kills it.
    _, metrics_bytes, commit_hash = _make_repo(tmp_path, declared_run=None)
    (tmp_path / PROVENANCE_MANIFEST_PATH).write_text(
        json.dumps(
            {
                "dirs": {
                    "run-1": {
                        "execution_id": DECLARED_RUN,
                        "commit_hash": "beefbeef" * 5,
                    }
                }
            }
        )
    )
    fake = FakeSeyvalClient(
        runs=[_completed(DECLARED_RUN, commit_hash)],
        stored={DECLARED_RUN: metrics_bytes},
    )
    result = await _verifier(fake).verify(str(tmp_path), {"run-1"})
    assert result.status == "mismatch"
    assert any("Seyval recorded" in c.detail for c in result.checks)


async def test_mismatch_when_local_metrics_tampered(tmp_path: Path) -> None:
    metrics_path, metrics_bytes, commit_hash = _make_repo(tmp_path)
    metrics_path.write_text(json.dumps({"accuracy": 0.971}))
    fake = FakeSeyvalClient(
        runs=[_completed(DECLARED_RUN, commit_hash)],
        stored={DECLARED_RUN: metrics_bytes},
    )
    result = await _verifier(fake).verify(str(tmp_path), {"run-1"})
    assert result.status == "mismatch"
    assert not result.checks[0].matched


async def test_mismatch_when_another_run_matches_but_declared_does_not(
    tmp_path: Path,
) -> None:
    # The pin is the point: bytes matching *some* completed run is not
    # enough — only the declared run counts.
    _, metrics_bytes, commit_hash = _make_repo(tmp_path)
    fake = FakeSeyvalClient(
        runs=[
            _completed(DECLARED_RUN, commit_hash),
            _completed("run-C", commit_hash),
        ],
        stored={
            DECLARED_RUN: json.dumps({"accuracy": 0.999}).encode(),
            "run-C": metrics_bytes,
        },
    )
    result = await _verifier(fake).verify(str(tmp_path), {"run-1"})
    assert result.status == "mismatch"
    assert result.checks[0].run_id == DECLARED_RUN
    assert "declared" in result.checks[0].detail


async def test_mismatch_when_commit_not_ancestor_of_head(tmp_path: Path) -> None:
    _, metrics_bytes, _ = _make_repo(tmp_path)
    foreign_commit = "deadbeef" * 5
    fake = FakeSeyvalClient(
        runs=[_completed(DECLARED_RUN, foreign_commit)],
        stored={DECLARED_RUN: metrics_bytes},
    )
    result = await _verifier(fake).verify(str(tmp_path), {"run-1"})
    assert result.status == "mismatch"
    assert result.checks[0].commit_in_history is False


async def test_mismatch_when_manifest_missing(tmp_path: Path) -> None:
    _, metrics_bytes, commit_hash = _make_repo(tmp_path, declared_run=None)
    fake = FakeSeyvalClient(
        runs=[_completed(DECLARED_RUN, commit_hash)],
        stored={DECLARED_RUN: metrics_bytes},
    )
    result = await _verifier(fake).verify(str(tmp_path), {"run-1"})
    assert result.status == "mismatch"
    assert "provenance" in result.checks[0].detail


async def test_mismatch_when_dir_not_declared(tmp_path: Path) -> None:
    _, metrics_bytes, commit_hash = _make_repo(tmp_path)
    fake = FakeSeyvalClient(
        runs=[_completed(DECLARED_RUN, commit_hash)],
        stored={DECLARED_RUN: metrics_bytes},
    )
    result = await _verifier(fake).verify(str(tmp_path), {"run-1", "run-2"})
    by_dir = {c.dir: c for c in result.checks}
    assert result.status == "mismatch"
    assert by_dir["run-1"].matched
    assert "declares no run" in by_dir["run-2"].detail


async def test_sibling_completed_runs_of_same_commit_are_listed(
    tmp_path: Path,
) -> None:
    _, metrics_bytes, commit_hash = _make_repo(tmp_path)
    fake = FakeSeyvalClient(
        runs=[
            _completed(DECLARED_RUN, commit_hash),
            _completed("run-C", commit_hash),
            _completed("run-other-code", "f" * 40),
            {"run_id": "run-D", "status": "failed", "commit_hash": commit_hash},
        ],
        stored={DECLARED_RUN: metrics_bytes},
    )
    result = await _verifier(fake).verify(str(tmp_path), {"run-1"})
    assert result.status == "verified"
    # Same code executed more than once: the selection must be reviewable.
    assert result.checks[0].sibling_run_ids == ["run-C"]


async def test_mismatch_when_declared_run_not_in_repository_listing(
    tmp_path: Path,
) -> None:
    # A run from another repository (or one that aged out of the capped
    # listing) cannot back the paper — only this repository's runs count.
    _, metrics_bytes, _ = _make_repo(tmp_path)
    fake = FakeSeyvalClient(runs=[], stored={DECLARED_RUN: metrics_bytes})
    result = await _verifier(fake).verify(str(tmp_path), {"run-1"})
    assert result.status == "mismatch"
    assert "not among this repository's" in result.checks[0].detail


async def test_unavailable_when_repository_not_registered(tmp_path: Path) -> None:
    _, metrics_bytes, commit_hash = _make_repo(tmp_path)
    fake = FakeSeyvalClient(
        runs=[_completed(DECLARED_RUN, commit_hash)],
        stored={DECLARED_RUN: metrics_bytes},
    )

    async def no_repos() -> list[dict[str, Any]]:
        return [{"id": "other", "git_url": "https://github.com/other/repo"}]

    fake.alist_repositories = no_repos
    result = await _verifier(fake).verify(str(tmp_path), {"run-1"})
    assert result.status == "unavailable"


async def test_mismatch_fails_verification_report(tmp_path: Path) -> None:
    metrics_path, metrics_bytes, commit_hash = _make_repo(tmp_path)
    metrics_path.write_text(json.dumps({"accuracy": 0.971}))
    fake = FakeSeyvalClient(
        runs=[_completed(DECLARED_RUN, commit_hash)],
        stored={DECLARED_RUN: metrics_bytes},
    )
    provenance = await _verifier(fake).verify(str(tmp_path), {"run-1"})

    report = verify_paper_record(str(tmp_path), "mdpi")  # missing files anyway
    report.ok = True  # isolate the provenance effect
    report = apply_provenance_result(report, provenance)
    assert report.ok is False
    assert report.provenance is not None
    assert report.provenance.source == "seyval"


def test_git_url_normalization_covers_common_origin_forms() -> None:
    from airas.infra.local_git import normalize_git_url as _normalize_git_url

    expected = "https://github.com/test-org/test-repo"
    assert _normalize_git_url("https://github.com/Test-Org/Test-Repo.git") == expected
    assert _normalize_git_url("git@github.com:test-org/test-repo.git") == expected
    assert _normalize_git_url("ssh://git@github.com/test-org/test-repo.git") == expected
    assert _normalize_git_url("ssh://git@github.com:22/test-org/test-repo") == expected


# ------------------------------------------ every file, and the parameters


def _write_manifest(tmp_path: Path, **dir_fields: Any) -> None:
    from airas.core.types.run_provenance import (
        PROVENANCE_MANIFEST_PATH,
        ResultsDirProvenance,
        RunProvenanceManifest,
    )

    manifest = RunProvenanceManifest(dirs={"run-1": ResultsDirProvenance(**dir_fields)})
    (tmp_path / PROVENANCE_MANIFEST_PATH).write_text(
        manifest.model_dump_json(indent=2) + "\n"
    )
    _git(tmp_path, "add", "-A")
    _git(tmp_path, "commit", "-q", "-m", "manifest")


async def test_every_file_in_the_directory_is_compared(tmp_path: Path) -> None:
    """Not only metrics.json: the inputs the metrics derive from too."""
    _, metrics_bytes, commit_hash = _make_repo(tmp_path)
    inputs = tmp_path / ".research" / "results" / "run-1" / "eval_inputs"
    inputs.mkdir()
    inputs_path = ".research/results/run-1/eval_inputs/task.json"
    (inputs / "task.json").write_bytes(b'{"predicted_labels": [1, 0]}')
    _git(tmp_path, "add", "-A")
    _git(tmp_path, "commit", "-q", "-m", "inputs")

    fake = FakeSeyvalClient(
        runs=[_completed(DECLARED_RUN, commit_hash)],
        stored={DECLARED_RUN: metrics_bytes},
        extra_outputs={inputs_path: b'{"predicted_labels": [1, 0]}'},
    )
    result = await _verifier(fake).verify(str(tmp_path), {"run-1"})
    assert result.status == "verified", result.checks[0].detail
    assert result.checks[0].files_checked == [
        inputs_path,
        ".research/results/run-1/metrics.json",
    ]

    # The metrics are untouched; only the inputs were edited.
    (inputs / "task.json").write_bytes(b'{"predicted_labels": [0, 0]}')
    result = await _verifier(fake).verify(str(tmp_path), {"run-1"})
    assert result.status == "mismatch"
    assert inputs_path in result.checks[0].detail


async def test_a_file_the_run_never_produced_is_a_mismatch(tmp_path: Path) -> None:
    _, metrics_bytes, commit_hash = _make_repo(tmp_path)
    (tmp_path / ".research" / "results" / "run-1" / "planted.json").write_text("{}")
    fake = FakeSeyvalClient(
        runs=[_completed(DECLARED_RUN, commit_hash)],
        stored={DECLARED_RUN: metrics_bytes},
    )
    result = await _verifier(fake).verify(str(tmp_path), {"run-1"})
    assert result.status == "mismatch"
    assert "produced no such file" in result.checks[0].detail


async def test_cached_parameters_must_match_the_dispatch(tmp_path: Path) -> None:
    """The manifest caches the dispatch so the record can be realized
    offline. A cache that says `full` while Seyval says `pilot` would confirm
    a declaration the run never satisfied."""
    _, metrics_bytes, commit_hash = _make_repo(tmp_path)
    _write_manifest(
        tmp_path,
        execution_id=DECLARED_RUN,
        commit_hash=commit_hash,
        overrides={"mode": "full"},
    )
    run = _completed(DECLARED_RUN, commit_hash)
    run["command_args"] = ["python", "-m", "src.main", "mode=pilot"]
    fake = FakeSeyvalClient(runs=[run], stored={DECLARED_RUN: metrics_bytes})

    result = await _verifier(fake).verify(str(tmp_path), {"run-1"})
    assert result.status == "mismatch"
    assert result.checks[0].parameters_match is False
    assert "differ from what Seyval recorded" in result.checks[0].detail


async def test_cached_parameters_that_match_are_reported_as_such(
    tmp_path: Path,
) -> None:
    _, metrics_bytes, commit_hash = _make_repo(tmp_path)
    _write_manifest(
        tmp_path,
        execution_id=DECLARED_RUN,
        commit_hash=commit_hash,
        overrides={"mode": "full"},
    )
    run = _completed(DECLARED_RUN, commit_hash)
    run["command_args"] = ["python", "-m", "src.main", "mode=full"]
    fake = FakeSeyvalClient(runs=[run], stored={DECLARED_RUN: metrics_bytes})

    result = await _verifier(fake).verify(str(tmp_path), {"run-1"})
    assert result.status == "verified", result.checks[0].detail
    assert result.checks[0].parameters_match is True
