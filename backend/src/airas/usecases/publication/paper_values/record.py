from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Iterator, Sequence, TypeVar

from pydantic import BaseModel

from airas.core.research_paths import RECORD_PATH
from airas.core.types.paper_values import TableSpec
from airas.core.types.research_record import (
    ChartDeclaration,
    ClaimDeclaration,
    DesignDeclaration,
    Hypothesis,
    ResearchRecord,
    RunDeclaration,
    RunResult,
)

T = TypeVar("T", bound=BaseModel)

# Layouts this airas no longer reads. Named so the failure says what the
# file is rather than that it is corrupt.
LEGACY_TOP_LEVEL_KEYS = ("prereg", "hypothesis", "schema_version")


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
    try:
        loaded = json.loads(raw)
    except json.JSONDecodeError as e:
        raise ValueError(f"{RECORD_PATH} is not valid JSON: {e}") from e
    if isinstance(loaded, dict) and "hypotheses" not in loaded:
        found = [k for k in LEGACY_TOP_LEVEL_KEYS if k in loaded]
        if found:
            raise ValueError(
                f"{RECORD_PATH} uses an earlier layout ({', '.join(found)}); "
                "this airas reads the hypotheses[] tree. There is no automatic "
                "migration — containment forbids one — so pin an older airas "
                "or start a new record."
            )
    return ResearchRecord.model_validate_json(raw)


def save_record(local_repo_path: str, record: ResearchRecord) -> Path:
    path = record_path(local_repo_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    # Defaults are omitted from the file (a run with no results yet, an
    # unset `withdrawn`) so the tree reads as what was declared. Containment
    # compares model dumps, not file text, so omission changes nothing there.
    path.write_text(
        record.model_dump_json(indent=2, exclude_defaults=True) + "\n",
        encoding="utf-8",
    )
    return path


# --------------------------------------------------------------------------
# Containment: the one rule that replaces every per-field append-only check.
#
# A newer record must contain its predecessor whole. Objects gain keys but
# never lose or change one; arrays are appended to, so the old array is a
# prefix of the new one. Rewriting a hypothesis, editing a frozen declaration,
# dropping an execution and reordering a list all fail the same way, so the
# check does not have to enumerate what may change.
#
# The single exception is `verified`, which is a fact the procedure sets
# from false to true once. That transition is permitted; the reverse is not.
# --------------------------------------------------------------------------

MONOTONE_KEY = "verified"
# Compared as a whole rather than key by key: a run's declared conditions
# are one declaration, and adding a condition later is as much a change as
# altering one. Letting `params` gain keys would let an empty declaration be
# filled in after the run.
LEAF_KEYS = frozenset({"params"})


def containment_violations(older: Any, newer: Any, path: str = "") -> list[str]:
    here = path or "(root)"

    if isinstance(older, dict) and path.rsplit(".", 1)[-1] in LEAF_KEYS:
        if older != newer:
            return [f"{here}: changed ({older!r} -> {newer!r})"]
        return []

    if isinstance(older, dict):
        if not isinstance(newer, dict):
            return [f"{here}: was an object, is now {type(newer).__name__}"]
        problems: list[str] = []
        for key, old_value in older.items():
            if key not in newer:
                problems.append(f"{here}.{key}: removed")
                continue
            child = f"{path}.{key}" if path else key
            if key == MONOTONE_KEY and old_value is False and newer[key] is True:
                continue
            problems += containment_violations(old_value, newer[key], child)
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
# Effective entries: with append order guaranteed, position carries what a
# `supersedes` field would — the last entry for an id is the live one, and
# `withdrawn` retires one without a replacement.
# --------------------------------------------------------------------------


def active(entries: Sequence[T], id_attr: str) -> list[T]:
    latest: dict[str, T] = {}
    for entry in entries:
        latest[getattr(entry, id_attr)] = entry
    return [e for e in latest.values() if not getattr(e, "withdrawn", False)]


def all_hypotheses(record: ResearchRecord) -> list[Hypothesis]:
    return active(record.hypotheses, "id")


def all_claims(record: ResearchRecord) -> Iterator[tuple[Hypothesis, ClaimDeclaration]]:
    for hypothesis in all_hypotheses(record):
        for claim in active(hypothesis.claims, "id"):
            yield hypothesis, claim


def claim_runs(
    claim: ClaimDeclaration,
) -> list[tuple[DesignDeclaration, RunDeclaration]]:
    return [
        (design, run)
        for design in active(claim.designs, "id")
        for run in active(design.runs, "run_id")
    ]


def all_runs(
    record: ResearchRecord,
) -> Iterator[tuple[Hypothesis, ClaimDeclaration, DesignDeclaration, RunDeclaration]]:
    for hypothesis, claim in all_claims(record):
        for design, run in claim_runs(claim):
            yield hypothesis, claim, design, run


def run_index(record: ResearchRecord) -> dict[str, RunDeclaration]:
    return {run.run_id: run for _, _, _, run in all_runs(record)}


def claim_index(record: ResearchRecord) -> dict[str, ClaimDeclaration]:
    return {claim.id: claim for _, claim in all_claims(record)}


def all_tables(record: ResearchRecord) -> list[TableSpec]:
    return [t for h in all_hypotheses(record) for t in active(h.tables, "key")]


def all_charts(record: ResearchRecord) -> list[ChartDeclaration]:
    return [c for h in all_hypotheses(record) for c in active(h.charts, "path")]


def selected_result(run: RunDeclaration) -> RunResult | None:
    """The result a realization reports for this run: the last one."""
    return run.results[-1] if run.results else None


# --------------------------------------------------------------------------
# Consistency: checkable at freeze time, before a single run exists.
# --------------------------------------------------------------------------


def record_consistency_problems(record: ResearchRecord) -> list[str]:
    problems: list[str] = []

    # Repeated ids at any level are revisions, not errors: the later entry
    # is the live one and containment keeps the earlier one readable. Run
    # ids are the exception — they address a results directory and must be
    # unique across the whole record.
    seen_runs: dict[str, str] = {}
    for hypothesis in record.hypotheses:
        for claim in hypothesis.claims:
            for design in claim.designs:
                for run in design.runs:
                    owner = f"{hypothesis.id}/{claim.id}/{design.id}"
                    if run.run_id in seen_runs and seen_runs[run.run_id] != owner:
                        problems.append(
                            f"run '{run.run_id}' is declared under both "
                            f"'{seen_runs[run.run_id]}' and '{owner}' — run ids "
                            "address a results directory and must be repo-unique"
                        )
                    seen_runs.setdefault(run.run_id, owner)

    for _, claim in all_claims(record):
        if not claim_runs(claim):
            problems.append(
                f"claim {claim.id}: declares no run — a claim with no "
                "experiment cannot be verified"
            )

    declared = set(run_index(record))
    for spec in all_tables(record):
        for row in spec.rows:
            if row.run_id not in declared and row.run_id != "comparison":
                problems.append(
                    f"table {spec.key}: row references run '{row.run_id}', "
                    "which no design declares"
                )
    return problems
