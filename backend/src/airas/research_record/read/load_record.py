from __future__ import annotations

from pathlib import Path

from airas.core.research_paths import (
    RECORD_PATH,
)
from airas.core.types.research_record import ResearchRecord


def record_path(local_repo_path: str) -> Path:
    return Path(local_repo_path).expanduser().resolve() / RECORD_PATH


def load_record(local_repo_path: str) -> ResearchRecord:
    path = record_path(local_repo_path)
    if not path.is_file():
        raise ValueError(f"{RECORD_PATH} not found under {path.parents[1]}")

    return ResearchRecord.model_validate_json(path.read_text(encoding="utf-8"))
