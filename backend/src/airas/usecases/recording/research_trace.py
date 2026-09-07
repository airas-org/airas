"""Step boundaries: the research trace and the fork-point commit.

`begin_step` records where a step starts; `end_step` captures the agent's
state into the repository and commits everything, making that commit a
fork point. The trace is advisory — never part of the record gate.

begin_step が「研究の状態」側を書き、end_step が「エージェントの状態」側を埋めて commit する
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
    read_pointer,
    transcript_files,
)


def _root(local_path: str) -> Path:
    return Path(local_path).expanduser().resolve()


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
    local_path: str,
    pointer: SessionPointer | None,
    trace: list[ResearchTraceEvent],
    reason: str | None,
) -> dict[str, Any] | None:
    # Only the first step this session takes in a forked repository compares
    # the live harness with the one the fork point was captured from.
    origin = _read_derived_from(local_path)
    if origin is None or any(
        e.session_id == (pointer and pointer.session_id) for e in trace
    ):
        return None
    diff: dict[str, Any] = {}
    if pointer is not None:
        try:
            source, _ = load_agent_state(local_path, origin.session_id)
            diff = harness_diff(
                source.harness, harness_state(pointer, transcript_files(pointer))
            )
        except FileNotFoundError:
            pass
    return {"agent": diff, "research": reason}


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def begin_step(
    local_path: str,
    step: str,
    run_ids: list[str] | None = None,
    reason: str | None = None,
) -> ResearchTraceEvent:
    trace = _read_trace(local_path)
    pointer = read_pointer(local_path)
    event = ResearchTraceEvent(
        kind="begin",
        step=step,
        iteration=sum(1 for e in trace if e.kind == "begin" and e.step == step) + 1,
        timestamp=_now(),
        head=head_commit(_root(local_path)),
        run_ids=run_ids or [],
        reason=reason,
        session_id=pointer.session_id if pointer else None,
        intervention=_intervention(local_path, pointer, trace, reason),
    )
    _append(local_path, event)
    return event


def end_step(
    local_path: str, step: str, reason: str | None = None
) -> tuple[ResearchTraceEvent, str | None]:
    trace = _read_trace(local_path)
    pointer = read_pointer(local_path)
    state_path = capture_agent_state(local_path, pointer)[1] if pointer else None
    event = ResearchTraceEvent(
        kind="end",
        step=step,
        iteration=max((e.iteration for e in trace if e.step == step), default=1),
        timestamp=_now(),
        head=head_commit(_root(local_path)),
        reason=reason,
        session_id=pointer.session_id if pointer else None,
        agent_state=state_path,
    )
    _append(local_path, event)
    commit = commit_paths(
        _root(local_path), ["."], f"step: end {step} #{event.iteration}"
    )
    return event, commit
