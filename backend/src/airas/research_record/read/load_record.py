from __future__ import annotations

from airas.core.research_paths import (
    RECORD_PATH,
    record_path,
)
from airas.core.types.research_record import ResearchRecord


def load_record(local_repo_path: str) -> ResearchRecord:
    path = record_path(local_repo_path)
    if not path.is_file():
        raise ValueError(f"{RECORD_PATH} not found under {path.parents[1]}")

    return ResearchRecord.model_validate_json(path.read_text(encoding="utf-8"))
