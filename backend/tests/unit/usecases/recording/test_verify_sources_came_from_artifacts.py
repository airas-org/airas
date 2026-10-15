"""Every .research/sources/<id>/ new to main is byte for byte its
fetch_literature.yml run's artifact entry, cited or not and whatever the
record claims it is; one on main never changes; and the record's fields for
an imported source are its metadata.json's. Anything else — a source the
agent wrote, an artifact of another workflow, an outage — fails the gate."""

import asyncio
import io
import json
import subprocess
import zipfile
from pathlib import Path
from typing import Any

import pytest

from airas.core.types.record_verification import RecordVerification
from airas.core.types.research_record import (
    LiteratureSource,
    Repository,
    ResearchRecord,
)
from airas.research_record.read.load_imported_source import imported_bibliography
from airas.research_record.verify._verify_sources_came_from_artifacts import (
    verify_sources_came_from_artifacts,
)


def _row(title: str) -> dict[str, Any]:
    return {
        "title": title,
        "authors": ["A. Author"],
        "doi": None,
        "arxiv_id": f"2401.0000{len(title)}v1",
        "url": "https://arxiv.org/abs/x",
        "published_date": "2024-01-02",
        "venue": None,
        "source": "arxiv",
        "fetched_at": "2026-10-15T00:00:00+00:00",
        "fulltext": {"url": "u", "parser": "pymupdf test", "fetched_at": "t"},
    }


OLD_ROW, NEW_ROW = _row("Old Paper"), _row("New Paper")
ENTRY = {"metadata.json": json.dumps(NEW_ROW).encode(), "fulltext.txt": b"page\fpage"}


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
    _write(repo, "s1", {"metadata.json": json.dumps(OLD_ROW).encode()})
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


def _imported(source_id: str, row: dict[str, Any], **changed: Any) -> LiteratureSource:
    """The source as preregister pins it from metadata.json, with `changed` forged."""
    return LiteratureSource(
        id=source_id,
        bibkey=f"key-{source_id}",
        **{**imported_bibliography(row), **changed},
    )


def _code(source_id: str) -> Repository:
    return Repository(
        id=f"{source_id}.r1", url="https://github.com/acme/trainer", commit="a" * 40
    )


def _record(*sources: LiteratureSource) -> ResearchRecord:
    return ResearchRecord(literature=list(sources))


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
    record = _record(_imported("s1", OLD_ROW), _imported("s2", NEW_ROW))
    statuses = _statuses(repo, record, _GitHub())
    assert statuses["literature[s2]"].status == "verified"
    assert (
        "literature[s1]" not in statuses
    )  # on main, unchanged: checked when it landed


def test_a_source_changed_after_it_reached_main_fails(tmp_path: Path) -> None:
    repo = _repo(tmp_path)
    _write(repo, "s1", {"fulltext.txt": b"added later"})
    _git(repo, "add", "-A")
    statuses = _statuses(repo, _record(_imported("s1", OLD_ROW)), _GitHub())
    assert statuses["literature[s1]"].status == "mismatch"
    assert "never changed once on main" in statuses["literature[s1]"].reason


def test_a_new_source_edited_after_the_import_fails(tmp_path: Path) -> None:
    repo = _repo(tmp_path)
    _write(repo, "s2", {"fulltext.txt": b"page\fa quote the paper never had"})
    status = _statuses(repo, _record(_imported("s2", NEW_ROW)), _GitHub())[
        "literature[s2]"
    ]
    assert status.status == "mismatch"
    assert "fulltext.txt differ" in status.reason


def test_a_source_the_agent_wrote_fails_even_while_nothing_cites_it(
    tmp_path: Path,
) -> None:
    """Merged uncited, it would be exempt on main by the time something cites it."""
    repo = _repo(tmp_path)
    _write(repo, "s3", ENTRY)
    status = _statuses(repo, _record(), _GitHub())[".research/sources/s3"]
    assert status.status == "mismatch"
    assert ".provenance.json" in status.reason


def test_a_source_claimed_to_predate_fetch_literature_is_still_compared(
    tmp_path: Path,
) -> None:
    repo = _repo(tmp_path)
    _write(repo, "s3", {"fulltext.txt": b"forged"})
    record = _record(
        LiteratureSource(id="s3", title="t", bibkey="k", verified_by="doi.org")
    )
    assert _statuses(repo, record, _GitHub())["literature[s3]"].status == "mismatch"


def test_an_imported_source_relabelled_as_code_is_still_compared(
    tmp_path: Path,
) -> None:
    repo = _repo(tmp_path)
    _write(repo, "s2", {"fulltext.txt": b"forged"})
    forged = _imported("s2", NEW_ROW, verified_by="git", repositories=[_code("s2")])
    reasons = [
        s.reason
        for s in _statuses_all(repo, _record(forged), _GitHub())
        if s.path == "literature[s2]"
    ]
    assert any("verified_by differ" in r for r in reasons)
    assert any("fulltext.txt differ" in r for r in reasons)


def _statuses_all(repo: Path, record: ResearchRecord, github: Any) -> list[Any]:
    verification = RecordVerification()
    asyncio.run(
        verify_sources_came_from_artifacts(repo, record, verification, lambda: github)
    )
    return verification.declaration_statuses


@pytest.mark.parametrize("source_id", ["s1", "s2"])
def test_a_record_field_that_is_not_the_fetched_metadata_fails(
    tmp_path: Path, source_id: str
) -> None:
    repo = _repo(tmp_path)
    row = OLD_ROW if source_id == "s1" else NEW_ROW
    record = _record(_imported(source_id, row, title="A Better Title"))
    reasons = [
        s.reason
        for s in _statuses_all(repo, record, _GitHub())
        if s.status == "mismatch"
    ]
    assert any("title differ from .research/sources" in r for r in reasons)


def test_a_cited_source_with_no_directory_fails(tmp_path: Path) -> None:
    repo = _repo(tmp_path)
    status = _statuses(repo, _record(_imported("s9", NEW_ROW)), _GitHub())[
        "literature[s9]"
    ]
    assert (status.status, status.reason) == (
        "mismatch",
        ".research/sources/s9 does not exist",
    )


def test_code_preregister_snapshotted_is_not_an_artifact(tmp_path: Path) -> None:
    repo = _repo(tmp_path)
    _write(repo, "s3", {"r1.txt": b"==> src/train.py <==\nlr = 3e-4\n"})
    record = _record(
        _imported("s2", NEW_ROW),
        LiteratureSource(
            id="s3",
            title="acme/trainer",
            bibkey="k",
            verified_by="git",
            repositories=[_code("s3")],
        ),
    )
    statuses = _statuses(repo, record, _GitHub())
    assert "literature[s3]" not in statuses
    assert statuses["literature[s2]"].status == "verified"


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
    status = _statuses(repo, _record(_imported("s2", NEW_ROW)), github)[
        "literature[s2]"
    ]
    assert status.status == "mismatch"
    assert reason in status.reason


def test_a_source_on_main_from_before_fetch_literature_is_not_its_concern(
    tmp_path: Path,
) -> None:
    repo = _repo(tmp_path)
    (repo / ".research" / "sources" / "s1" / "metadata.json").unlink()
    _write(repo, "s1", {"fulltext.txt": b"pinned before fetch_literature.yml"})
    _git(repo, "add", "-A")
    _git(repo, "commit", "-qam", "drop metadata")
    _git(repo, "update-ref", "refs/remotes/origin/main", "HEAD")
    record = _record(
        LiteratureSource(id="s1", title="t", bibkey="k", verified_by="doi.org"),
        _imported("s2", NEW_ROW),
    )
    assert "literature[s1]" not in _statuses(repo, record, _GitHub())


def test_a_source_whose_file_links_elsewhere_fails(tmp_path: Path) -> None:
    """Linked to a file outside sources/, its text could change with no diff under it."""
    repo = tmp_path
    _git(repo, "init", "-q")
    _git(repo, "config", "user.email", "test@example.com")
    _git(repo, "config", "user.name", "test")
    _git(repo, "remote", "add", "origin", "https://github.com/acme/exp")
    (repo / "notes.txt").write_text("page\fpage")
    _write(repo, "s1", {"metadata.json": json.dumps(OLD_ROW).encode()})
    (repo / ".research" / "sources" / "s1" / "fulltext.txt").symlink_to(
        repo / "notes.txt"
    )
    _git(repo, "add", "-A")
    _git(repo, "commit", "-q", "-m", "main")
    _git(repo, "update-ref", "refs/remotes/origin/main", "HEAD")
    (repo / "notes.txt").write_text("page\fa quote the paper never had")

    reasons = [
        s.reason
        for s in _statuses_all(repo, _record(_imported("s1", OLD_ROW)), _GitHub())
        if s.status == "mismatch"
    ]
    assert any("holds a symlink" in r for r in reasons)


def test_a_paper_labelled_as_code_is_not_exempt(tmp_path: Path) -> None:
    repo = _repo(tmp_path)
    _write(repo, "s3", {"fulltext.txt": b"forged text"})
    forged = LiteratureSource(
        id="s3",
        title="A Paper",
        bibkey="k",
        doi="10.1/forged",
        verified_by="git",
        repositories=[_code("s3")],
    )
    status = _statuses(repo, _record(forged), _GitHub())["literature[s3]"]
    assert status.status == "mismatch"
    assert ".provenance.json" in status.reason
