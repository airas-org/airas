"""A fork point: a commit that carries the agent's state along with the
research, so the same step can be resumed from a clone — by the same
harness (Claude Code resume) or another one (neutral messages)."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest

from airas.core.research_paths import SESSIONS_DIR, STEPS_PATH
from airas.core.types.agent_state import SessionPointer
from airas.core.types.research_trace import DerivedFromRepository
from airas.usecases.recording import agent_state as agent_state_module
from airas.usecases.recording.agent_state import (
    load_agent_state,
    neutral_messages,
    pointer_from_hook,
    read_pointer,
    render_handoff,
    restore_claude_session,
    write_pointer,
)
from airas.usecases.recording.codex_hooks import install_codex_hooks
from airas.usecases.recording.research_trace import (
    capture,
    is_experiment_repository,
    record_step,
    write_derived_from,
)

SESSION = "11111111-2222-3333-4444-555555555555"


def _git(repo: Path, *args: str) -> str:
    return subprocess.run(
        ["git", "-C", str(repo), *args], check=True, capture_output=True, text=True
    ).stdout.strip()


@pytest.fixture
def homes(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> dict[str, Path]:
    homes = {name: tmp_path / name for name in ("airas", "claude", "codex")}
    monkeypatch.setattr(agent_state_module, "POINTER_DIR", homes["airas"] / "sessions")
    monkeypatch.setattr(agent_state_module, "CLAUDE_HOME", homes["claude"])
    monkeypatch.setattr(agent_state_module, "CODEX_HOME", homes["codex"])
    return homes


@pytest.fixture
def repo(tmp_path: Path) -> Path:
    repo = tmp_path / "exp"
    repo.mkdir()
    _git(repo, "init", "-q")
    _git(repo, "config", "user.email", "t@example.com")
    _git(repo, "config", "user.name", "t")
    (repo / "CLAUDE.md").write_text("tracked instructions\n")
    (repo / ".research").mkdir()
    (repo / ".research" / "record.json").write_text("{}")
    _git(repo, "add", ".")
    _git(repo, "commit", "-q", "-m", "init")
    return repo


def _claude_session(homes: dict[str, Path], repo: Path) -> SessionPointer:
    # A Claude Code session as the harness records it: the main transcript,
    # one subagent, memory, settings holding a secret, and a plugin.
    project = agent_state_module._claude_project_dir(str(repo))
    lines = [
        {
            "type": "user",
            "uuid": "u1",
            "parentUuid": None,
            "cwd": str(repo),
            "sessionId": SESSION,
            "message": {"role": "user", "content": "start"},
        },
        {
            "type": "assistant",
            "uuid": "a1",
            "parentUuid": "u1",
            "cwd": str(repo),
            "sessionId": SESSION,
            "version": "2.1.263",
            "message": {
                "role": "assistant",
                "model": "claude-fable-5-1",
                "content": [
                    {
                        "type": "tool_use",
                        "id": "t1",
                        "name": "Bash",
                        "input": {"command": "ls"},
                    }
                ],
            },
        },
        {
            "type": "user",
            "uuid": "u2",
            "parentUuid": "a1",
            "cwd": str(repo),
            "sessionId": SESSION,
            "message": {
                "role": "user",
                "content": [
                    {"type": "tool_result", "tool_use_id": "t1", "content": "ok"}
                ],
            },
        },
    ]
    main = project / f"{SESSION}.jsonl"
    main.parent.mkdir(parents=True, exist_ok=True)
    main.write_text("\n".join(json.dumps(x) for x in lines) + "\n")
    sub = project / SESSION / "subagents" / "agent-abc.jsonl"
    sub.parent.mkdir(parents=True, exist_ok=True)
    sub.write_text(
        json.dumps(
            {
                "type": "assistant",
                "uuid": "s1",
                "cwd": str(repo),
                "message": {"role": "assistant", "content": "sub"},
            }
        )
        + "\n"
    )
    (project / "memory").mkdir(exist_ok=True)
    (project / "memory" / "note.md").write_text("remember this\n")
    (homes["claude"] / "settings.json").write_text(
        '{"env": {"OPENAI_API_KEY": "sk-secret"}}'
    )
    plugin = homes["claude"] / "plugin"
    (plugin / "skills" / "s").mkdir(parents=True, exist_ok=True)
    (plugin / "skills" / "s" / "SKILL.md").write_text("skill\n")
    (plugin / ".claude-plugin").mkdir(exist_ok=True)
    (plugin / ".claude-plugin" / "plugin.json").write_text('{"version": "0.3.1"}')
    return pointer_from_hook(
        "claude",
        {
            "session_id": SESSION,
            "cwd": str(repo),
            "transcript_path": str(main),
            "model": "claude-fable-5-1",
            "plugin_root": str(plugin),
        },
    )


def test_session_id_must_be_a_plain_name() -> None:
    for bad in ("../x", "a/b", "..", ""):
        with pytest.raises(ValueError):
            pointer_from_hook("claude", {"session_id": bad, "cwd": "/tmp"})


def test_hook_pointer_round_trips(homes: dict[str, Path], repo: Path) -> None:
    pointer = _claude_session(homes, repo)
    write_pointer(pointer)
    assert read_pointer(str(repo)) == pointer
    assert read_pointer(str(repo / "elsewhere")) is None


def test_capture_commits_the_agent_state(homes: dict[str, Path], repo: Path) -> None:
    pointer = _claude_session(homes, repo)
    write_pointer(pointer)
    record_step(str(repo), pointer, "write-experiment-code")
    (repo / "src.py").write_text("print(1)\n")
    before = _git(repo, "rev-parse", "HEAD")

    event, commit = capture(str(repo), pointer)

    assert commit and commit != before and commit == _git(repo, "rev-parse", "HEAD")
    assert _git(repo, "status", "--porcelain") == ""
    state, path = load_agent_state(str(repo))
    assert event.agent_state and path == repo / event.agent_state
    assert state.harness.model == "claude-fable-5-1"
    assert state.harness.version == "2.1.263"
    assert state.harness.plugin and state.harness.plugin.version == "0.3.1"
    assert state.harness.memory == {"note.md": "remember this\n"}
    assert (
        "sk-secret" not in state.harness.files[str(homes["claude"] / "settings.json")]
    )
    assert str(repo / "CLAUDE.md") not in state.harness.files  # already tracked
    assert [Path(t).name for t in state.session.transcripts] == [
        f"{SESSION}.jsonl",
        "agent-abc.jsonl",
    ]
    assert all((repo / t).is_file() for t in state.session.transcripts)

    events = [json.loads(line) for line in (repo / STEPS_PATH).read_text().splitlines()]
    assert [e["kind"] for e in events] == ["step", "capture"]
    assert events[0]["step"] == "write-experiment-code" and events[0]["head"] == before


def test_entering_a_step_again_counts_iterations(
    homes: dict[str, Path], repo: Path
) -> None:
    pointer = _claude_session(homes, repo)
    record_step(str(repo), pointer, "run-experiments")
    capture(str(repo), pointer)
    event = record_step(str(repo), pointer, "run-experiments")
    assert event.iteration == 2


def test_hooks_ignore_clones_without_research(tmp_path: Path) -> None:
    assert not is_experiment_repository(str(tmp_path))


def test_restore_rebinds_the_transcript_to_the_clone(
    homes: dict[str, Path], repo: Path, tmp_path: Path
) -> None:
    capture(str(repo), _claude_session(homes, repo))
    clone = tmp_path / "clone"
    _git(repo, "clone", "-q", str(repo), str(clone))

    state, _ = load_agent_state(str(clone))
    new_id, project = restore_claude_session(str(clone), state)

    restored = (project / f"{new_id}.jsonl").read_text()
    assert new_id != SESSION and SESSION not in restored
    assert str(clone) in restored and str(repo) not in restored
    assert (project / new_id / "subagents" / "agent-abc.jsonl").is_file()
    assert (project / "memory" / "note.md").read_text() == "remember this\n"


def test_neutral_messages_and_handoff(homes: dict[str, Path], repo: Path) -> None:
    capture(str(repo), _claude_session(homes, repo))
    state, _ = load_agent_state(str(repo))
    messages = neutral_messages(str(repo), state)
    assert [m["role"] for m in messages] == ["user", "assistant", "user", "assistant"]
    assert messages[1]["content"][0]["type"] == "tool_use"
    assert messages[3]["agent_id"] == "agent-abc"
    handoff = render_handoff(state, messages)
    assert "tool_use Bash" in handoff and "remember" not in handoff


def test_codex_rollout_reads_as_neutral_messages(
    homes: dict[str, Path], repo: Path
) -> None:
    rollout = (
        homes["codex"]
        / "sessions"
        / "2026"
        / "09"
        / "07"
        / f"rollout-x-{SESSION}.jsonl"
    )
    rollout.parent.mkdir(parents=True)
    rows = [
        {
            "type": "session_meta",
            "payload": {"cli_version": "0.153.2", "cwd": str(repo)},
        },
        {"type": "turn_context", "payload": {"model": "gpt-5.6-sol"}},
        {
            "type": "response_item",
            "payload": {
                "type": "custom_tool_call",
                "name": "exec",
                "call_id": "c1",
                "input": "ls",
            },
        },
        {
            "type": "response_item",
            "payload": {
                "type": "custom_tool_call_output",
                "call_id": "c1",
                "output": "ok",
            },
        },
        {
            "type": "response_item",
            "payload": {
                "type": "message",
                "role": "assistant",
                "content": [{"type": "output_text", "text": "done"}],
            },
        },
    ]
    rollout.write_text("\n".join(json.dumps(r) for r in rows) + "\n")
    capture(
        str(repo), pointer_from_hook("codex", {"session_id": SESSION, "cwd": str(repo)})
    )
    state, _ = load_agent_state(str(repo))
    assert state.harness.kind == "codex" and state.harness.version == "0.153.2"
    assert state.harness.model == "gpt-5.6-sol"
    parts = [m["content"][0]["type"] for m in neutral_messages(str(repo), state)]
    assert parts == ["tool_use", "tool_result", "text"]
    with pytest.raises(ValueError):
        restore_claude_session(str(repo), state)


def test_first_event_after_a_fork_records_the_intervention(
    homes: dict[str, Path], repo: Path, tmp_path: Path
) -> None:
    origin_commit = capture(str(repo), _claude_session(homes, repo))[1]
    clone = tmp_path / "fork"
    _git(repo, "clone", "-q", str(repo), str(clone))
    write_derived_from(
        str(clone),
        DerivedFromRepository(commit=origin_commit or "", session_id=SESSION),
    )
    # The forker's harness: same transcript layout, a different model and session.
    forker = _claude_session(homes, clone).model_copy(
        update={"session_id": "s2", "model": "claude-opus-5"}
    )

    first = record_step(str(clone), forker, "write-experiment-code")
    second = capture(str(clone), forker)[0]

    assert first.intervention == {
        "model": {"from": "claude-fable-5-1", "to": "claude-opus-5"}
    }
    assert second.intervention is None


def test_install_codex_hooks_is_idempotent(tmp_path: Path) -> None:
    home = tmp_path / "codex"
    (home).mkdir()
    (home / "config.toml").write_text('[projects."/x"]\ntrust_level = "trusted"\n')
    install_codex_hooks(home)
    install_codex_hooks(home)
    hooks = json.loads((home / "hooks.json").read_text())
    assert len(hooks["hooks"]["SessionStart"]) == 1
    assert len(hooks["hooks"]["Stop"]) == 1
    config = (home / "config.toml").read_text()
    assert "codex_hooks = true" in config and 'trust_level = "trusted"' in config


def test_sessions_dir_is_where_the_docs_say() -> None:
    assert SESSIONS_DIR == ".research/sessions"
