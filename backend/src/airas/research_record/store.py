"""Where record.json lives, and reading, writing and committing it."""

from __future__ import annotations

from pathlib import Path

from airas.core.research_paths import RECORD_PATH
from airas.core.types.research_record import ResearchRecord
from airas.infra.local_git import commit_paths


def record_path(local_repo_path: str) -> Path:
    return Path(local_repo_path).expanduser().resolve() / RECORD_PATH


def load_record(local_repo_path: str) -> ResearchRecord:
    path = record_path(local_repo_path)
    if not path.is_file():
        raise ValueError(f"{RECORD_PATH} not found under {path.parents[1]}")

    return ResearchRecord.model_validate_json(path.read_text(encoding="utf-8"))


def save_record(local_repo_path: str, record: ResearchRecord) -> Path:
    path = record_path(local_repo_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    # Defaults are omitted so the file reads as what was declared; containment
    # compares model dumps, not text, so omission changes nothing there.
    path.write_text(
        record.model_dump_json(indent=2, exclude_defaults=True) + "\n",
        encoding="utf-8",
    )
    return path


def commit_record_paths(local_path: str, paths: list[str], message: str) -> str:
    commit = commit_paths(Path(local_path).expanduser().resolve(), paths, message)
    if commit is None:
        raise ValueError(
            "files were written but git commit failed — the record must live "
            "in a git clone with a commit identity configured"
        )
    return commit
