"""The committed history only grows: each record.json version contains its parent, and the import-time hashes in the provenance manifest never change under the same execution."""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path
from typing import Any

from pydantic import ValidationError

from airas.core.research_paths import RECORD_PATH
from airas.core.types.record_verification import RecordVerification
from airas.core.types.research_record import ResearchRecord
from airas.core.types.run_provenance import (
    PROVENANCE_MANIFEST_PATH,
    RunProvenanceManifest,
)
from airas.infra.local_git import commits_with_parents, file_bytes_at_commit, is_shallow
from airas.research_record.read.read_run_outputs import load_provenance_manifest

MONOTONE_KEY = "verified"

VERDICT_KEY = "verdict"

# Compared as a whole rather than key by key: a run's declared conditions
# are one declaration, and adding a condition later is as much a change as
# altering one. Letting `params` gain keys would let an empty declaration be
# filled in after the run.
LEAF_KEYS = frozenset({"params"})


def _verify_append_only(
    root: Path,
    record: ResearchRecord,
    check_version: Callable[[ResearchRecord, RecordVerification], None],
) -> list[str] | None:
    """Problems, or None when there is no history to check."""
    if is_shallow(root):
        return None
    edges = commits_with_parents(root, RECORD_PATH)
    if edges is None:
        return None

    # The record as of each commit involved. Absent counts as empty, so a
    # deletion is a shrink and a first creation contains nothing to lose.
    versions: dict[str, ResearchRecord] = {}
    for commit_hash in {h for commit, parents in edges for h in (commit, *parents)}:
        raw = file_bytes_at_commit(root, commit_hash, RECORD_PATH)
        if raw is None:
            versions[commit_hash] = ResearchRecord()
            continue
        try:
            versions[commit_hash] = ResearchRecord.model_validate_json(raw)
        except ValidationError:
            return [f"record.json at {commit_hash[:12]} is not a valid record"]

    # A declaration may only name passages already in the record when it
    # lands: a passage registered afterwards was not what it was grounded on.
    problems = []
    for commit_hash, version in versions.items():
        checked = RecordVerification()
        check_version(version, checked)
        problems += [f"{commit_hash[:12]}: {problem}" for problem in checked.problems]
    # Each commit against each of its parents — not against its neighbour in
    # a linear list, which would set two sibling branches against each other.
    problems += [
        f"{parent[:12]} -> {commit[:12]}: {problem}"
        for commit, parents in edges
        for parent in parents
        for problem in _containment_violations(
            versions[parent].model_dump(), versions[commit].model_dump()
        )
    ]
    head = file_bytes_at_commit(root, "HEAD", RECORD_PATH)
    committed = (
        ResearchRecord() if head is None else ResearchRecord.model_validate_json(head)
    )
    problems += [
        f"HEAD -> worktree: {problem}"
        for problem in _containment_violations(
            committed.model_dump(), record.model_dump()
        )
    ]
    return problems


def _verify_manifest_history(root: Path, require_history: bool) -> list[str]:
    """An import-time hash may not change under the same execution: once the
    backend drops the run, the hashes are all the gate has left."""
    if not (root / PROVENANCE_MANIFEST_PATH).is_file():
        return []
    unavailable = (
        [
            f"{PROVENANCE_MANIFEST_PATH}'s history could not be checked (shallow "
            "clone or no git history) — CI must check out with fetch-depth: 0"
        ]
        if require_history
        else []
    )
    if is_shallow(root):
        return unavailable
    edges = commits_with_parents(root, PROVENANCE_MANIFEST_PATH)
    if edges is None:
        return unavailable

    def manifest_at(commit_hash: str) -> RunProvenanceManifest:
        raw = file_bytes_at_commit(root, commit_hash, PROVENANCE_MANIFEST_PATH)
        try:
            return (
                RunProvenanceManifest()
                if raw is None
                else RunProvenanceManifest.model_validate_json(raw)
            )
        except ValidationError:
            return RunProvenanceManifest()

    versions = {
        h: manifest_at(h) for commit, parents in edges for h in (commit, *parents)
    }
    pairs = [
        (parent, commit, versions[parent], versions[commit])
        for commit, parents in edges
        for parent in parents
    ]
    worktree = load_provenance_manifest(root) or RunProvenanceManifest()
    pairs.append(("HEAD", "worktree", manifest_at("HEAD"), worktree))

    problems = []
    for older_hash, newer_hash, older, newer in pairs:
        for dir_name, old_entry in older.dirs.items():
            new_entry = newer.dirs.get(dir_name)
            edge = f"{older_hash[:12]} -> {newer_hash[:12]}: {PROVENANCE_MANIFEST_PATH}"
            if new_entry is None:
                problems.append(f"{edge} dropped the declaration for {dir_name}")
            elif (
                new_entry.execution_id == old_entry.execution_id
                and old_entry.files
                and new_entry.files != old_entry.files
            ):
                problems.append(
                    f"{edge} changed the import-time hashes of {dir_name} "
                    "under the same execution"
                )
    return problems


def _containment_violations(older: Any, newer: Any, path: str = "") -> list[str]:
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
            if key == VERDICT_KEY and old_value is None:
                continue
            problems += _containment_violations(old_value, newer[key], child)
        return problems

    if isinstance(older, list):
        if not isinstance(newer, list):
            return [f"{here}: was a list, is now {type(newer).__name__}"]
        if len(newer) < len(older):
            return [f"{here}: entries were removed ({len(older)} -> {len(newer)})"]
        problems = []
        for index, (old_item, new_item) in enumerate(zip(older, newer, strict=False)):
            problems += _containment_violations(old_item, new_item, f"{path}[{index}]")
        return problems

    if older != newer:
        return [f"{here}: changed ({older!r} -> {newer!r})"]
    return []


def verify_record_git_history(
    root: Path,
    record: ResearchRecord,
    require_history: bool,
    check_version: Callable[[ResearchRecord, RecordVerification], None],
    verification: RecordVerification,
) -> None:
    problems = _verify_append_only(root, record, check_version)
    if problems is None:
        verification.append_declaration_status(
            RECORD_PATH,
            "record.json's append-only history could not be checked (shallow "
            "clone or no git history) — CI must check out with fetch-depth: 0",
            "mismatch" if require_history else "skipped",
            evidence_path=RECORD_PATH,
        )
    else:
        for problem in problems:
            verification.append_declaration_status(
                RECORD_PATH, problem, "mismatch", evidence_path=RECORD_PATH
            )
        if not problems:
            verification.append_declaration_status(
                RECORD_PATH,
                "every committed version contains its parent and names only passages it held",
                "ok",
                evidence_path=RECORD_PATH,
            )
    for problem in _verify_manifest_history(root, require_history):
        verification.append_declaration_status(
            PROVENANCE_MANIFEST_PATH,
            problem,
            "mismatch",
            evidence_path=PROVENANCE_MANIFEST_PATH,
        )
