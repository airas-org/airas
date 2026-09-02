from __future__ import annotations

from pathlib import Path
from typing import Any, Sequence, TypeVar

from pydantic import BaseModel

from airas.core.research_paths import RECORD_PATH
from airas.core.types.paper_record import PaperRecord, PreregSection, RunResult
from airas.core.types.run_provenance import RunProvenanceManifest

T = TypeVar("T", bound=BaseModel)

# (list field, identity attribute) of every declaration list in PreregSection.
DECLARATION_LISTS = [
    ("runs", "run_id"),
    ("claims", "id"),
    ("values", "key"),
    ("tables", "key"),
    ("charts", "path"),
]


def record_path(local_repo_path: str) -> Path:
    return Path(local_repo_path).expanduser().resolve() / RECORD_PATH


def load_record(local_repo_path: str) -> PaperRecord:
    path = record_path(local_repo_path)
    if not path.is_file():
        raise ValueError(
            f"{RECORD_PATH} not found under {path.parents[1]} "
            "(preregister_record creates it)"
        )
    return PaperRecord.model_validate_json(path.read_text(encoding="utf-8"))


def save_record(local_repo_path: str, record: PaperRecord) -> Path:
    path = record_path(local_repo_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(record.model_dump_json(indent=2) + "\n", encoding="utf-8")
    return path


def collect_run_results(
    metrics_data: dict[str, Any], manifest: RunProvenanceManifest | None
) -> list[RunResult]:
    return [
        RunResult(
            run_id=dir_name,
            execution_id=declared.execution_id if declared else None,
            run_commit=declared.commit_hash if declared else None,
            metrics=metrics_data[dir_name],
        )
        for dir_name in sorted(metrics_data)
        for declared in [manifest.dirs.get(dir_name) if manifest else None]
    ]


def active(entries: Sequence[T], id_attr: str) -> list[T]:
    superseded = {
        getattr(e, "supersedes", None)
        for e in entries
        if getattr(e, "supersedes", None)
    }
    return [e for e in entries if getattr(e, id_attr) not in superseded]


def prereg_append_violations(older: PreregSection, newer: PreregSection) -> list[str]:
    problems: list[str] = []
    for field in ("hypothesis", "design"):
        if getattr(older, field) != getattr(newer, field):
            problems.append(f"{field} was rewritten")

    for field, id_attr in DECLARATION_LISTS:
        old_list = getattr(older, field)
        new_list = getattr(newer, field)
        if len(new_list) < len(old_list):
            problems.append(f"{field}: entries were removed")
            continue
        for old_entry, new_entry in zip(old_list, new_list, strict=False):
            if old_entry.model_dump() != new_entry.model_dump():
                problems.append(
                    f"{field} entry '{getattr(old_entry, id_attr)}' was modified"
                )
    if newer.notes[: len(older.notes)] != older.notes:
        problems.append("notes: existing entries were modified or removed")
    return problems


def prereg_consistency_problems(prereg: PreregSection) -> list[str]:
    problems: list[str] = []
    for field, id_attr in DECLARATION_LISTS:
        entries: list[Any] = getattr(prereg, field)
        ids = [getattr(e, id_attr) for e in entries]

        for duplicate in sorted({i for i in ids if ids.count(i) > 1}):
            problems.append(f"{field}: duplicate '{duplicate}'")

        for entry in entries:
            if entry.supersedes and entry.supersedes not in ids:
                problems.append(
                    f"{field}: '{getattr(entry, id_attr)}' supersedes "
                    f"unknown '{entry.supersedes}'"
                )

    run_ids = {r.run_id for r in prereg.runs}
    value_keys = {v.key for v in prereg.values}
    for claim in prereg.claims:
        for run_id in claim.run_ids:
            if run_id not in run_ids:
                problems.append(f"claim {claim.id}: run '{run_id}' is not declared")

        for key in claim.value_keys:
            if key not in value_keys:
                problems.append(f"claim {claim.id}: value key '{key}' is not declared")
    return problems
