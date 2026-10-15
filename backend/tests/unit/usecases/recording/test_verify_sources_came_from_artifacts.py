"""A source CI imported is, while it is new to main, byte for byte its
fetch_literature.yml run's artifact entry; once on main it never changes.
Anything else — a source the agent wrote, an artifact of another workflow,
an outage — fails the gate."""

import asyncio
import io
import json
import subprocess
import zipfile
from pathlib import Path
from typing import Any

import pytest

from airas.core.types.record_verification import RecordVerification
from airas.core.types.research_record import LiteratureSource, ResearchRecord
from airas.research_record.verify._verify_sources_came_from_artifacts import (
    verify_sources_came_from_artifacts,
)

ENTRY = {"metadata.json": b'{"title": "New Paper"}', "fulltext.txt": b"page\fpage"}


def _git(repo: Path, *args: str) -> None:
    subprocess.run(["git", "-C", str(repo), *args], capture_output=True, check=True)


def _write(repo: Path, source_id: str, files: dict[str, bytes]) -> None:
    source_dir = repo / ".research" / "sources" / source_id
    source_dir.mkdir(parents=True, exist_ok=True)
    for name, content in files.items():
        (source_dir / name).write_bytes(content)


def _repo(tmp_path: Path) -> Path:
    """s1 already on main; s2 new on the branch, imported from run 7 entry 0."""
    repo = tmp_path
    _git(repo, "init", "-q")
    _git(repo, "config", "user.email", "test@example.com")
    _git(repo, "config", "user.name", "test")
    _git(repo, "remote", "add", "origin", "https://github.com/acme/exp")
    _write(repo, "s1", {"metadata.json": b'{"title": "Old Paper"}'})
    _git(repo, "add", "-A")
    _git(repo, "commit", "-q", "-m", "main")
    _git(repo, "update-ref", "refs/remotes/origin/main", "HEAD")
    _write(repo, "s2", ENTRY)
    (repo / ".research" / "sources" / ".provenance.json").write_text(
        json.dumps({"s2": {"workflow_run_id": "7", "entry": "0"}})
    )
    _git(repo, "add", "-A")
    _git(repo, "commit", "-q", "-m", "import run 7")
    return repo


def _record(*source_ids: str) -> ResearchRecord:
    return ResearchRecord(
        literature=[
            LiteratureSource(id=s, title=s, bibkey=f"key-{s}", verified_by="arxiv")
            for s in source_ids
        ]
    )


def _zip(entries: dict[str, dict[str, bytes]]) -> bytes:
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as zipped:
        for entry, files in entries.items():
            for name, content in files.items():
                zipped.writestr(f"{entry}/{name}", content)
    return buffer.getvalue()


class _GitHub:
    def __init__(
        self,
        *,
        path: str = ".github/workflows/fetch_literature.yml",
        conclusion: str = "success",
        expired: bool = False,
        entries: dict[str, dict[str, bytes]] | None = None,
    ) -> None:
        self.run = {"path": path, "conclusion": conclusion}
        self.expired = expired
        self.entries = {"0": ENTRY} if entries is None else entries

    async def aget_workflow_run(self, owner: str, repo: str, run_id: int) -> Any:
        assert (owner, repo, run_id) == ("acme", "exp", 7)
        return self.run

    async def alist_workflow_run_artifacts(self, owner: str, repo: str, run_id: int):
        return {
            "artifacts": [{"name": "literature-7", "id": 1, "expired": self.expired}]
        }

    async def adownload_artifact_archive(self, owner: str, repo: str, artifact_id: int):
        return _zip(self.entries)


def _statuses(repo: Path, record: ResearchRecord, github: Any) -> dict[str, Any]:
    verification = RecordVerification()

    def factory() -> Any:
        if isinstance(github, Exception):
            raise github
        return github

    asyncio.run(verify_sources_came_from_artifacts(repo, record, verification, factory))
    return {s.path: s for s in verification.declaration_statuses}


def test_a_new_source_that_is_its_artifact_entry_is_verified(tmp_path: Path) -> None:
    repo = _repo(tmp_path)
    statuses = _statuses(repo, _record("s1", "s2"), _GitHub())
    assert statuses["literature[s2]"].status == "verified"
    assert (
        "literature[s1]" not in statuses
    )  # on main and unchanged: checked when it landed


def test_a_source_changed_after_it_reached_main_fails(tmp_path: Path) -> None:
    repo = _repo(tmp_path)
    (repo / ".research" / "sources" / "s1" / "metadata.json").write_text(
        '{"title": "x"}'
    )
    statuses = _statuses(repo, _record("s1"), _GitHub())
    assert statuses["literature[s1]"].status == "mismatch"
    assert "never changed once on main" in statuses["literature[s1]"].reason


def test_a_new_source_edited_after_the_import_fails(tmp_path: Path) -> None:
    repo = _repo(tmp_path)
    _write(repo, "s2", {"fulltext.txt": b"page\fa quote the paper never had"})
    status = _statuses(repo, _record("s2"), _GitHub())["literature[s2]"]
    assert status.status == "mismatch"
    assert "fulltext.txt differ" in status.reason


def test_a_source_the_agent_wrote_without_a_run_fails(tmp_path: Path) -> None:
    repo = _repo(tmp_path)
    _write(repo, "s3", ENTRY)
    status = _statuses(repo, _record("s3"), _GitHub())["literature[s3]"]
    assert status.status == "mismatch"
    assert ".provenance.json" in status.reason


@pytest.mark.parametrize(
    ("github", "reason"),
    [
        (
            _GitHub(path=".github/workflows/run_experiment.yml"),
            "not .github/workflows/fetch_literature.yml",
        ),
        (_GitHub(conclusion="failure"), "did not succeed"),
        (_GitHub(expired=True), "has expired"),
        (_GitHub(entries={"1": ENTRY}), "has no entry 0"),
        (RuntimeError("GH_PERSONAL_ACCESS_TOKEN is not set"), "is not set"),
    ],
)
def test_a_new_source_its_run_does_not_vouch_for_fails(
    tmp_path: Path, github: Any, reason: str
) -> None:
    repo = _repo(tmp_path)
    status = _statuses(repo, _record("s2"), github)["literature[s2]"]
    assert status.status == "mismatch"
    assert reason in status.reason


def test_code_and_sources_from_before_fetch_literature_are_not_its_concern(
    tmp_path: Path,
) -> None:
    repo = _repo(tmp_path)
    record = ResearchRecord(
        literature=[
            LiteratureSource(id="s2", title="t", bibkey="k", verified_by="doi.org")
        ]
    )
    assert _statuses(repo, record, _GitHub()) == {}
