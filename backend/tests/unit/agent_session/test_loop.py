"""`airas loop` ends the session with an exit code the workflow can act on."""

import subprocess
from pathlib import Path

import pytest

from airas.agent_session import loop as loop_module


def _fake_run(claude_exit: int, gh: subprocess.CompletedProcess):
    def run(cmd, **kwargs):
        if cmd[0] == "claude":
            return subprocess.CompletedProcess(cmd, claude_exit)
        if cmd[0] == "gh":
            return gh
        raise AssertionError(cmd)

    return run


def _start(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, run) -> None:
    policy = tmp_path / "policy.md"
    policy.write_text("# policy\n")
    (tmp_path / "repo").mkdir()
    monkeypatch.setattr(loop_module.subprocess, "run", run)
    monkeypatch.setattr(
        loop_module, "remote_origin_url", lambda clone: "https://github.com/o/r"
    )
    loop_module.loop("", str(tmp_path), "o", None, str(policy))


def test_archived_repository_counts_as_failure(tmp_path, monkeypatch) -> None:
    gh = subprocess.CompletedProcess(["gh"], 0, stdout="true\n", stderr="")
    with pytest.raises(SystemExit) as exit_:
        _start(tmp_path, monkeypatch, _fake_run(0, gh))
    assert exit_.value.code == 1


def test_a_finished_research_exits_zero(tmp_path, monkeypatch) -> None:
    gh = subprocess.CompletedProcess(["gh"], 0, stdout="false\n", stderr="")
    with pytest.raises(SystemExit) as exit_:
        _start(tmp_path, monkeypatch, _fake_run(0, gh))
    assert exit_.value.code == 0


def test_an_unreadable_archive_status_is_an_error_not_a_pass(
    tmp_path, monkeypatch
) -> None:
    gh = subprocess.CompletedProcess(["gh"], 1, stdout="", stderr="HTTP 401")
    with pytest.raises(RuntimeError, match="archive status"):
        _start(tmp_path, monkeypatch, _fake_run(0, gh))


def _resume(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, ls_remote_exit: int
) -> list:
    policy = tmp_path / "policy.md"
    policy.write_text("# policy\n")
    calls: list = []

    def run(cmd, **kwargs):
        calls.append(cmd[:4])
        if cmd[0] == "git" and "ls-remote" in cmd:
            return subprocess.CompletedProcess(
                cmd, ls_remote_exit, stdout=b"", stderr=b""
            )
        if cmd[0] == "git":
            return subprocess.CompletedProcess(cmd, 0)
        if cmd[0] == "claude":
            return subprocess.CompletedProcess(cmd, 0)
        if cmd[0] == "gh":
            return subprocess.CompletedProcess(cmd, 0, stdout="false\n", stderr="")
        raise AssertionError(cmd)

    monkeypatch.setattr(loop_module.subprocess, "run", run)
    monkeypatch.setattr(loop_module, "load_agent_state", lambda clone: ({}, None))
    monkeypatch.setattr(
        loop_module, "restore_claude_session", lambda clone, state: ("sid", None)
    )
    monkeypatch.setattr(
        loop_module, "remote_origin_url", lambda clone: "https://github.com/o/r"
    )
    with pytest.raises(SystemExit) as exit_:
        loop_module.loop(
            "https://github.com/o/r", str(tmp_path), "o", None, str(policy)
        )
    assert exit_.value.code == 0
    return calls


def test_resume_fast_forwards_the_staging_ref_when_it_exists(
    tmp_path, monkeypatch
) -> None:
    calls = _resume(tmp_path, monkeypatch, ls_remote_exit=0)
    assert ["git", "-C", str(tmp_path / "repo"), "fetch"] in calls
    assert ["git", "-C", str(tmp_path / "repo"), "merge"] in calls


def test_resume_without_a_staging_ref_is_not_a_failure(tmp_path, monkeypatch) -> None:
    calls = _resume(tmp_path, monkeypatch, ls_remote_exit=2)
    assert not any(c[3:] == ["fetch"] for c in calls)


def test_resume_fails_when_the_remote_cannot_be_read(tmp_path, monkeypatch) -> None:
    with pytest.raises(subprocess.CalledProcessError):
        _resume(tmp_path, monkeypatch, ls_remote_exit=128)


def test_a_policy_with_placeholders_is_refused(tmp_path) -> None:
    policy = tmp_path / "policy.md"
    policy.write_text("compute_id: <fill in>\n")
    with pytest.raises(SystemExit, match="fill in"):
        loop_module.loop("", str(tmp_path), "o", None, str(policy))
