"""The access event records which registered source files a tool call
touched, and nothing else: a read anywhere else leaves no trace."""

import json
import subprocess
from pathlib import Path

from airas.agent_session.research_trace import record_access
from airas.core.research_paths import STEPS_PATH
from airas.core.types.agent_state import SessionPointer


def _repo(tmp_path: Path) -> Path:
    subprocess.run(["git", "-C", str(tmp_path), "init", "-q"], check=True)
    (tmp_path / ".research" / "sources" / "s1").mkdir(parents=True)
    (tmp_path / ".research" / "sources" / "s1" / "fulltext.txt").write_text("text")
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "main.py").write_text("print()")
    return tmp_path


def _pointer(repo: Path) -> SessionPointer:
    return SessionPointer(harness="claude", session_id="abc123", cwd=str(repo))


def test_a_read_of_a_registered_source_is_recorded(tmp_path: Path) -> None:
    repo = _repo(tmp_path)

    event = record_access(
        str(repo), _pointer(repo), [str(repo / ".research/sources/s1/fulltext.txt")]
    )

    assert event is not None
    assert event.kind == "access"
    assert event.paths == [".research/sources/s1/fulltext.txt"]
    lines = (repo / STEPS_PATH).read_text().splitlines()
    assert json.loads(lines[-1])["paths"] == [".research/sources/s1/fulltext.txt"]


def test_reads_outside_the_sources_directory_are_not_recorded(tmp_path: Path) -> None:
    repo = _repo(tmp_path)

    event = record_access(
        str(repo), _pointer(repo), [str(repo / "src/main.py"), "/etc/hosts"]
    )

    assert event is None
    assert not (repo / STEPS_PATH).exists()


def test_relative_paths_and_duplicates_are_normalised(tmp_path: Path) -> None:
    repo = _repo(tmp_path)

    event = record_access(
        str(repo),
        _pointer(repo),
        [
            ".research/sources/s1/fulltext.txt",
            str(repo / ".research/sources/s1/fulltext.txt"),
        ],
    )

    assert event is not None
    assert event.paths == [".research/sources/s1/fulltext.txt"]
