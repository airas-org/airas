from __future__ import annotations

import hashlib
import json
import re
import shutil
import uuid
from pathlib import Path
from typing import Any

from airas.core.research_paths import SESSIONS_DIR
from airas.core.types.agent_state import (
    AgentState,
    Harness,
    HarnessState,
    PluginRef,
    SessionPointer,
    SessionState,
)
from airas.infra.local_git import is_tracked

POINTER_DIR = Path("~/.airas/sessions").expanduser()
CLAUDE_HOME = Path("~/.claude").expanduser()
CODEX_HOME = Path("~/.codex").expanduser()
AGENT_STATE_FILENAME = "agent_state.json"

_SECRET = re.compile(
    r"(?i)(\"?[\w.-]*(?:key|token|secret|password)[\w.-]*\"?\s*[:=]\s*)(\"[^\"]*\"|\S+)"
)


# ---------------------------------------------------------------- pointer
# airas hook session-start が書き、airas hook capture が読む live セッションの所在。


def _pointer_path(cwd: str) -> Path:
    digest = hashlib.sha256(str(Path(cwd).resolve()).encode()).hexdigest()[:16]
    return POINTER_DIR / f"{digest}.json"


def write_pointer(pointer: SessionPointer) -> Path:
    path = _pointer_path(pointer.cwd)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(pointer.model_dump_json(indent=2))
    return path


def read_pointer(cwd: str) -> SessionPointer | None:
    path = _pointer_path(cwd)
    if not path.is_file():
        return None
    return SessionPointer.model_validate_json(path.read_text())


def pointer_from_hook(harness: Harness, payload: dict[str, Any]) -> SessionPointer:
    # Both harnesses send session_id, transcript_path, cwd and model on
    # SessionStart; the plugin root is Claude Code's hook environment.
    return SessionPointer(
        harness=harness,
        session_id=payload["session_id"],
        cwd=payload.get("cwd") or str(Path.cwd()),
        transcript_path=payload.get("transcript_path"),
        model=payload.get("model"),
        plugin_root=payload.get("plugin_root"),
    )


# ---------------------------------------------------------------- capture
# airas hook capture が使う側。ポインタからトランスクリプトと設定を集め、
# .research/sessions/<harness>/<session_id>/ に AgentState として書く。


def _claude_project_dir(cwd: str) -> Path:
    return CLAUDE_HOME / "projects" / re.sub(r"[^A-Za-z0-9]", "-", str(cwd))


def transcript_files(pointer: SessionPointer) -> list[Path]:
    if pointer.harness == "claude":
        main = (
            Path(pointer.transcript_path)
            if pointer.transcript_path
            else _claude_project_dir(pointer.cwd) / f"{pointer.session_id}.jsonl"
        )
        subagents = main.parent / pointer.session_id / "subagents"
        return [p for p in [main, *sorted(subagents.glob("*.jsonl"))] if p.is_file()]
    if pointer.transcript_path and Path(pointer.transcript_path).is_file():
        return [Path(pointer.transcript_path)]
    return sorted(
        (CODEX_HOME / "sessions").glob(f"**/rollout-*-{pointer.session_id}.jsonl")
    )


def _mask(text: str) -> str:
    return _SECRET.sub(r'\1"***"', text)


def _read_files(paths: list[Path], root: Path | None = None) -> dict[str, str]:
    # Files the repository already tracks are not copied again.
    return {
        str(p): _mask(p.read_text(errors="replace"))
        for p in paths
        if p.is_file() and not (root and is_tracked(root, p))
    }


def _plugin_ref(root: str | None) -> PluginRef | None:
    if not root or not Path(root).is_dir():
        return None
    base = Path(root)
    digest = hashlib.sha256()
    for path in sorted(p for p in (base / "skills").rglob("*") if p.is_file()):
        digest.update(str(path.relative_to(base)).encode())
        digest.update(path.read_bytes())
    manifest = base / ".claude-plugin" / "plugin.json"
    version = (
        json.loads(manifest.read_text()).get("version") if manifest.is_file() else None
    )
    return PluginRef(root=root, version=version, skills_sha256=digest.hexdigest())


def _first_json(path: Path, predicate: Any) -> dict[str, Any]:
    with path.open() as f:
        for line in f:
            try:
                obj = json.loads(line)
            except json.JSONDecodeError:
                continue
            if predicate(obj):
                return obj
    return {}


def harness_state(pointer: SessionPointer, transcripts: list[Path]) -> HarnessState:
    repo = Path(pointer.cwd)
    if pointer.harness == "claude":
        first = (
            _first_json(transcripts[0], lambda o: o.get("type") == "assistant")
            if transcripts
            else {}
        )
        project = _claude_project_dir(pointer.cwd)
        return HarnessState(
            kind="claude",
            version=first.get("version"),
            model=pointer.model or (first.get("message") or {}).get("model"),
            files=_read_files(
                [
                    CLAUDE_HOME / "settings.json",
                    CLAUDE_HOME / "CLAUDE.md",
                    repo / ".claude" / "settings.json",
                    repo / ".claude" / "settings.local.json",
                    repo / "CLAUDE.md",
                    repo / ".claude" / "CLAUDE.md",
                    repo / ".claude" / "CLAUDE.local.md",
                    *sorted((repo / ".claude" / "rules").glob("*.md")),
                ],
                repo,
            ),
            memory={
                p.name: p.read_text() for p in sorted((project / "memory").glob("*.md"))
            },
            plugin=_plugin_ref(pointer.plugin_root),
        )
    meta = (
        _first_json(transcripts[0], lambda o: o.get("type") == "session_meta")
        if transcripts
        else {}
    )
    turn = (
        _first_json(transcripts[0], lambda o: o.get("type") == "turn_context")
        if transcripts
        else {}
    )
    return HarnessState(
        kind="codex",
        version=(meta.get("payload") or {}).get("cli_version"),
        model=pointer.model or (turn.get("payload") or {}).get("model"),
        files=_read_files(
            [CODEX_HOME / "config.toml", CODEX_HOME / "AGENTS.md", repo / "AGENTS.md"],
            repo,
        ),
        plugin=_plugin_ref(pointer.plugin_root),
    )


def _state_dir(local_path: str, harness: Harness, session_id: str) -> Path:
    return Path(local_path).expanduser().resolve() / SESSIONS_DIR / harness / session_id


def capture_agent_state(
    local_path: str, pointer: SessionPointer
) -> tuple[AgentState, str]:
    """Copy the live session into the repository; returns the state and the
    repo-relative path of agent_state.json."""
    root = Path(local_path).expanduser().resolve()
    target = _state_dir(local_path, pointer.harness, pointer.session_id)
    target.mkdir(parents=True, exist_ok=True)
    sources = transcript_files(pointer)
    copied: list[str] = []
    for source in sources:
        dest = target / (
            "subagents/" + source.name if "subagents" in source.parts else source.name
        )
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, dest)
        copied.append(str(dest.relative_to(root)))
    state = AgentState(
        harness=harness_state(pointer, sources),
        session=SessionState(session_id=pointer.session_id, transcripts=copied),
    )
    state_path = target / AGENT_STATE_FILENAME
    state_path.write_text(state.model_dump_json(indent=2, exclude_defaults=True))
    return state, str(state_path.relative_to(root))


# ---------------------------------------------------------------- diff
# 派生後の最初の hook イベントで、fork 点のハーネスと live のハーネスを比べる。


def harness_diff(before: HarnessState, after: HarnessState) -> dict[str, Any]:
    """What changed between two harness configurations, by field."""

    def digest(files: dict[str, str]) -> dict[str, str]:
        return {
            k: hashlib.sha256(v.encode()).hexdigest()[:12] for k, v in files.items()
        }

    a = {
        "kind": before.kind,
        "version": before.version,
        "model": before.model,
        "plugin": before.plugin.model_dump() if before.plugin else None,
        "files": digest(before.files),
        "memory": digest(before.memory),
    }
    b = {
        "kind": after.kind,
        "version": after.version,
        "model": after.model,
        "plugin": after.plugin.model_dump() if after.plugin else None,
        "files": digest(after.files),
        "memory": digest(after.memory),
    }
    return {k: {"from": a[k], "to": b[k]} for k in a if a[k] != b[k]}


# ---------------------------------------------------------------- restore
# airas session import / export が使う側。clone の AgentState から
# 中立形式の messages、handoff.md、Claude Code の resume 可能なセッションを作る。


def _list_agent_states(local_path: str) -> list[Path]:
    root = Path(local_path).expanduser().resolve() / SESSIONS_DIR
    return sorted(
        root.glob(f"*/*/{AGENT_STATE_FILENAME}"), key=lambda p: p.stat().st_mtime
    )


def load_agent_state(
    local_path: str, session_id: str | None = None
) -> tuple[AgentState, Path]:
    """The named session's state, or the most recently written one."""
    paths = _list_agent_states(local_path)
    if session_id:
        paths = [p for p in paths if p.parent.name == session_id]
    if not paths:
        raise FileNotFoundError(
            f"no agent state under {SESSIONS_DIR} in {local_path}"
            + (f" for session {session_id}" if session_id else "")
        )
    path = paths[-1]
    return AgentState.model_validate_json(path.read_text()), path


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    out = []
    for line in path.read_text().splitlines():
        try:
            out.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return out


def neutral_messages(local_path: str, state: AgentState) -> list[dict[str, Any]]:
    """The session as a harness-neutral message list: role, content parts
    (text / thinking / tool_use / tool_result), ids and timestamps."""
    root = Path(local_path).expanduser().resolve()
    messages: list[dict[str, Any]] = []
    for rel in state.session.transcripts:
        agent = Path(rel).stem if "/subagents/" in rel else None
        for obj in _read_jsonl(root / rel):
            parsed = (
                _claude_message(obj)
                if state.harness.kind == "claude"
                else _codex_message(obj)
            )
            if parsed:
                messages.append({**parsed, **({"agent_id": agent} if agent else {})})
    return messages


def _claude_message(obj: dict[str, Any]) -> dict[str, Any] | None:
    if obj.get("type") not in ("user", "assistant"):
        return None
    message = obj.get("message") or {}
    content = message.get("content")
    parts = [{"type": "text", "text": content}] if isinstance(content, str) else content
    return {
        "role": message.get("role", obj["type"]),
        "content": parts or [],
        "id": obj.get("uuid"),
        "parent_id": obj.get("parentUuid"),
        "timestamp": obj.get("timestamp"),
    }


def _codex_message(obj: dict[str, Any]) -> dict[str, Any] | None:
    if obj.get("type") != "response_item":
        return None
    p = obj.get("payload") or {}
    kind = p.get("type")
    base = {"id": p.get("id") or p.get("call_id"), "timestamp": obj.get("timestamp")}
    if kind == "message":
        parts = [
            {"type": "text", "text": c.get("text", "")} for c in p.get("content") or []
        ]
        return {"role": p.get("role", "assistant"), "content": parts, **base}
    if kind == "reasoning":
        text = "\n".join(s.get("text", "") for s in p.get("summary") or [])
        return {
            "role": "assistant",
            "content": [{"type": "thinking", "text": text}],
            **base,
        }
    if kind in ("function_call", "custom_tool_call"):
        raw = p.get("arguments") if kind == "function_call" else p.get("input")
        try:
            args = json.loads(raw) if isinstance(raw, str) else raw
        except json.JSONDecodeError:
            args = {"raw": raw}
        part = {
            "type": "tool_use",
            "id": p.get("call_id"),
            "name": p.get("name"),
            "input": args,
        }
        return {"role": "assistant", "content": [part], **base}
    if kind in ("function_call_output", "custom_tool_call_output"):
        part = {
            "type": "tool_result",
            "tool_use_id": p.get("call_id"),
            "content": p.get("output"),
        }
        return {"role": "user", "content": [part], **base}
    return None


def render_handoff(state: AgentState, messages: list[dict[str, Any]]) -> str:
    """The neutral messages as one Markdown document, for a harness that
    cannot resume the raw transcript."""
    lines = [
        f"# Session {state.session.session_id} ({state.harness.kind}, "
        f"{state.harness.model or 'model unknown'})",
        "",
        "Continue this research from where the transcript below ends.",
        "",
    ]
    for m in messages:
        who = m["role"] + (f" [{m['agent_id']}]" if m.get("agent_id") else "")
        for part in m["content"]:
            kind = part.get("type")
            if kind in ("text", "thinking"):
                lines += [f"## {who} ({kind})", part.get("text", ""), ""]
            elif kind == "tool_use":
                lines += [
                    f"## {who} (tool_use {part.get('name')})",
                    "```json",
                    json.dumps(part.get("input"), ensure_ascii=False, indent=2),
                    "```",
                    "",
                ]
            elif kind == "tool_result":
                body = part.get("content")
                text = (
                    body
                    if isinstance(body, str)
                    else json.dumps(body, ensure_ascii=False)
                )
                lines += [f"## {who} (tool_result)", "```", text, "```", ""]
    return "\n".join(lines)


def restore_claude_session(local_path: str, state: AgentState) -> tuple[str, Path]:
    """Write the transcripts back where Claude Code looks for them, bound to
    this clone and a fresh session id; returns (session_id, project dir)."""
    if state.harness.kind != "claude":
        raise ValueError(
            f"cannot resume a {state.harness.kind} transcript in Claude Code"
        )
    root = Path(local_path).expanduser().resolve()
    project = _claude_project_dir(str(root))
    project.mkdir(parents=True, exist_ok=True)
    new_id = str(uuid.uuid4())
    old_id = state.session.session_id
    main = _read_jsonl(root / state.session.transcripts[0])
    old_cwd = next((m["cwd"] for m in main if m.get("cwd")), None)
    for rel in state.session.transcripts:
        text = (root / rel).read_text().replace(old_id, new_id)
        if old_cwd:
            text = text.replace(old_cwd, str(root))
        dest = (
            project / new_id / "subagents" / Path(rel).name
            if "/subagents/" in rel
            else project / f"{new_id}.jsonl"
        )
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(text)
    memory = project / "memory"
    memory.mkdir(exist_ok=True)
    for name, body in state.harness.memory.items():
        (memory / name).write_text(body)
    return new_id, project
