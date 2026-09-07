"""The research trace and the fork-point commit, driven by harness hooks.

SessionStart → session-start: where the live session is (SessionPointer)
PostToolUse(Skill) → step: which step the agent entered
Stop → capture: AgentState into the repository, then commit the tree —
that commit is a fork point.

The trace is advisory — never part of the record gate.
"""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from airas.core.research_paths import DERIVED_FROM_PATH, STEPS_PATH
from airas.core.types.agent_state import SessionPointer
from airas.core.types.research_trace import DerivedFromRepository, ResearchTraceEvent
from airas.infra.local_git import commit_paths, head_commit
from airas.usecases.recording.agent_state import (
    capture_agent_state,
    harness_diff,
    harness_state,
    load_agent_state,
    transcript_files,
)


def _root(local_path: str) -> Path:
    return Path(local_path).expanduser().resolve()


def is_experiment_repository(local_path: str) -> bool:
    # Hooks fire in every session of the harness; only a clone with a
    # .research/ directory is a research the trace belongs to.
    return (_root(local_path) / ".research").is_dir()


def _read_trace(local_path: str) -> list[ResearchTraceEvent]:
    path = _root(local_path) / STEPS_PATH
    if not path.is_file():
        return []
    return [
        ResearchTraceEvent.model_validate_json(line)
        for line in path.read_text().splitlines()
        if line.strip()
    ]


def _append(local_path: str, event: ResearchTraceEvent) -> None:
    path = _root(local_path) / STEPS_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a") as f:
        f.write(event.model_dump_json(exclude_defaults=True) + "\n")


def _read_derived_from(local_path: str) -> DerivedFromRepository | None:
    path = _root(local_path) / DERIVED_FROM_PATH
    return (
        DerivedFromRepository.model_validate_json(path.read_text())
        if path.is_file()
        else None
    )


def write_derived_from(local_path: str, origin: DerivedFromRepository) -> Path:
    path = _root(local_path) / DERIVED_FROM_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(origin.model_dump_json(indent=2, exclude_defaults=True))
    return path


def _intervention(
    local_path: str, pointer: SessionPointer, trace: list[ResearchTraceEvent]
) -> dict[str, Any] | None:
    # Only this session's first event in a forked repository compares the
    # live harness with the one the fork point was captured from.
    origin = _read_derived_from(local_path)
    if origin is None or any(e.session_id == pointer.session_id for e in trace):
        return None
    try:
        source, _ = load_agent_state(local_path, origin.session_id)
    except FileNotFoundError:
        return {}
    return harness_diff(
        source.harness, harness_state(pointer, transcript_files(pointer))
    )


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def record_step(
    local_path: str, pointer: SessionPointer, step: str
) -> ResearchTraceEvent:
    trace = _read_trace(local_path)
    event = ResearchTraceEvent(
        kind="step",
        timestamp=_now(),
        session_id=pointer.session_id,
        head=head_commit(_root(local_path)),
        step=step,
        iteration=sum(1 for e in trace if e.kind == "step" and e.step == step) + 1,
        intervention=_intervention(local_path, pointer, trace),
    )
    _append(local_path, event)
    return event


def capture(
    local_path: str, pointer: SessionPointer
) -> tuple[ResearchTraceEvent, str | None]:
    """Capture the agent state, record it and commit the whole working
    tree; returns the event and the fork-point commit (None if nothing
    changed or the commit failed)."""
    trace = _read_trace(local_path)
    event = ResearchTraceEvent(
        kind="capture",
        timestamp=_now(),
        session_id=pointer.session_id,
        head=head_commit(_root(local_path)),
        agent_state=capture_agent_state(local_path, pointer)[1],
        intervention=_intervention(local_path, pointer, trace),
    )
    _append(local_path, event)
    commit = commit_paths(
        _root(local_path), ["."], f"capture: session {pointer.session_id[:8]}"
    )
    return event, commit
