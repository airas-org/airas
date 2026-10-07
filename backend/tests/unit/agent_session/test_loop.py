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


def test_a_policy_with_placeholders_is_refused(tmp_path) -> None:
    policy = tmp_path / "policy.md"
    policy.write_text("compute_id: <fill in>\n")
    with pytest.raises(SystemExit, match="fill in"):
        loop_module.loop("", str(tmp_path), "o", None, str(policy))
