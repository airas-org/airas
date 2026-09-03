from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Sequence, TypeVar

from pydantic import BaseModel

from airas.core.research_paths import RECORD_PATH
from airas.core.types.research_record import (
    RECORD_SCHEMA_VERSION,
    DesignDeclaration,
    Execution,
    ResearchRecord,
    RunDeclaration,
)

T = TypeVar("T", bound=BaseModel)


def record_path(local_repo_path: str) -> Path:
    return Path(local_repo_path).expanduser().resolve() / RECORD_PATH


def load_record(local_repo_path: str) -> ResearchRecord:
    path = record_path(local_repo_path)
    if not path.is_file():
        raise ValueError(
            f"{RECORD_PATH} not found under {path.parents[1]} "
            "(preregister_record creates it)"
        )
    raw = path.read_text(encoding="utf-8")
    # A v1 record is structurally different (prereg/results rather than a
    # hypothesis tree). Say so plainly instead of failing with a validation
    # error that reads like the record is corrupt.
    version = json.loads(raw).get("schema_version")
    if version is not None and version < RECORD_SCHEMA_VERSION:
        raise ValueError(
            f"{RECORD_PATH} is schema_version {version}, this airas reads "
            f"{RECORD_SCHEMA_VERSION}. The v{version} layout (prereg/results "
            "with a values registry) has no automatic migration yet — pin an "
            f"airas that reads v{version}, or start a new record."
        )
    return ResearchRecord.model_validate_json(raw)


def save_record(local_repo_path: str, record: ResearchRecord) -> Path:
    path = record_path(local_repo_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(record.model_dump_json(indent=2) + "\n", encoding="utf-8")
    return path


# --------------------------------------------------------------------------
# Containment: the one rule that replaces every per-field append-only check.
#
# A newer record must contain its predecessor whole. Objects gain keys but
# never lose or change one; arrays are appended to, so the old array is a
# prefix of the new one. Rewriting a hypothesis, editing a frozen criterion,
# dropping an execution and reordering a list all fail the same way, so the
# check does not have to enumerate what may change.
#
# This is why lists are held in append order rather than sorted: sorting
# would let a new entry land in the middle and break the prefix.
# --------------------------------------------------------------------------


def containment_violations(older: Any, newer: Any, path: str = "") -> list[str]:
    here = path or "(root)"

    if isinstance(older, dict):
        if not isinstance(newer, dict):
            return [f"{here}: was an object, is now {type(newer).__name__}"]
        problems: list[str] = []
        for key, old_value in older.items():
            if key not in newer:
                problems.append(f"{here}.{key}: removed")
                continue
            problems += containment_violations(
                old_value, newer[key], f"{path}.{key}" if path else key
            )
        return problems

    if isinstance(older, list):
        if not isinstance(newer, list):
            return [f"{here}: was a list, is now {type(newer).__name__}"]
        if len(newer) < len(older):
            return [f"{here}: entries were removed ({len(older)} -> {len(newer)})"]
        problems = []
        for index, (old_item, new_item) in enumerate(zip(older, newer, strict=False)):
            problems += containment_violations(old_item, new_item, f"{path}[{index}]")
        return problems

    if older != newer:
        return [f"{here}: changed ({older!r} -> {newer!r})"]
    return []


def record_append_violations(older: ResearchRecord, newer: ResearchRecord) -> list[str]:
    """Every committed revision must contain the one before it, whole."""
    return containment_violations(older.model_dump(), newer.model_dump())


# --------------------------------------------------------------------------
# Effective entries: with append order guaranteed, position carries what
# `supersedes` used to say — the last entry for an id is the live one, and
# `withdrawn` retires one without a replacement.
# --------------------------------------------------------------------------


def active(entries: Sequence[T], id_attr: str) -> list[T]:
    latest: dict[str, T] = {}
    for entry in entries:
        latest[getattr(entry, id_attr)] = entry
    return [e for e in latest.values() if not getattr(e, "withdrawn", False)]


def all_runs(record: ResearchRecord) -> list[tuple[DesignDeclaration, RunDeclaration]]:
    return [
        (design, run)
        for design in active(record.hypothesis.designs, "id")
        for run in active(design.runs, "run_id")
    ]


def run_index(record: ResearchRecord) -> dict[str, RunDeclaration]:
    return {run.run_id: run for _, run in all_runs(record)}


def selected_execution(run: RunDeclaration) -> Execution | None:
    """The execution a realization reports for this run.

    The last one, so re-running appends without rewriting history; which one
    was actually used is recorded per evaluation, so the paper's number stays
    traceable to a single execution even when several exist.
    """
    return run.executions[-1] if run.executions else None


# --------------------------------------------------------------------------
# Consistency: checkable at freeze time, before a single run exists.
# --------------------------------------------------------------------------


def ref_run_id(ref: str) -> str:
    return ref.split(".", 1)[0]


def record_consistency_problems(record: ResearchRecord) -> list[str]:
    problems: list[str] = []

    design_ids = [d.id for d in record.hypothesis.designs]
    for duplicate in sorted({i for i in design_ids if design_ids.count(i) > 1}):
        problems.append(f"designs: duplicate id '{duplicate}'")

    seen_runs: dict[str, str] = {}
    for design in record.hypothesis.designs:
        for run in design.runs:
            if run.run_id in seen_runs and seen_runs[run.run_id] != design.id:
                problems.append(
                    f"run '{run.run_id}' is declared in both "
                    f"'{seen_runs[run.run_id]}' and '{design.id}' — run ids "
                    "address a results directory and must be repo-unique"
                )
            seen_runs.setdefault(run.run_id, design.id)

    # Repeated claim ids are not an error: a later entry is the revision of
    # an earlier one, and containment keeps the earlier version readable.
    declared = set(run_index(record))
    referenced: set[str] = set()
    for claim in active(record.hypothesis.claims, "id"):
        for ref in claim.target.refs:
            run_id = ref_run_id(ref)
            referenced.add(run_id)
            if run_id not in declared and run_id != "comparison":
                problems.append(
                    f"claim {claim.id}: target references run '{run_id}', "
                    "which no design declares"
                )
        if claim.target.op in ("diff", "pct_improve") and len(claim.target.refs) != 2:
            problems.append(
                f"claim {claim.id}: op '{claim.target.op}' takes exactly 2 refs, "
                f"got {len(claim.target.refs)}"
            )
        if claim.criterion.min is None and claim.criterion.max is None:
            problems.append(f"claim {claim.id}: criterion is unbounded")

    for spec in active(record.tables, "key"):
        for row in spec.rows:
            if row.run_id not in declared and row.run_id != "comparison":
                problems.append(
                    f"table {spec.key}: row references run '{row.run_id}', "
                    "which no design declares"
                )
    return problems


def override_problems(record: ResearchRecord) -> list[str]:
    """Did each run execute with the overrides it declared?

    The commit fixes the config files but not the dispatch, so a run declared
    as `mode=full` can be executed as `mode=pilot` with the tree untouched —
    a fifth of the planned scale, reported as if it were the whole thing.
    Comparing the declaration against what the execution resolved is the only
    place that shows up.
    """
    problems: list[str] = []
    for run in run_index(record).values():
        execution = selected_execution(run)
        if execution is None or not run.overrides:
            continue
        for key, declared in run.overrides.items():
            # execution.overrides comes from the manifest, i.e. from the argv
            # Seyval recorded — the experiment code cannot write it, so a
            # mismatch here is a real divergence between plan and dispatch.
            actual = execution.overrides.get(key, execution.config.get(key))
            if actual is None:
                problems.append(
                    f"run '{run.run_id}': declared override '{key}={declared}' "
                    "is absent from the execution"
                )
            elif str(actual) != str(declared):
                problems.append(
                    f"run '{run.run_id}': declared '{key}={declared}' but "
                    f"executed '{key}={actual}'"
                )
    return problems


def orphan_runs(record: ResearchRecord) -> list[str]:
    """Declared runs no active claim references.

    Not an error — supporting numbers quoted in prose are legitimate — but
    listed, because an experiment nobody declared a reason for is where
    undeclared exploration would otherwise sit unnoticed.
    """
    referenced = {
        ref_run_id(ref)
        for claim in active(record.hypothesis.claims, "id")
        for ref in claim.target.refs
    }
    for spec in active(record.tables, "key"):
        referenced |= {row.run_id for row in spec.rows}
    return sorted(set(run_index(record)) - referenced)
