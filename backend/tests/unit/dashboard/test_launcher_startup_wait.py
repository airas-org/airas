"""A slow start is not a failed start, and must not be killed like one.

Two runs of `open_in_overleaf` failed with "Dashboard did not become
healthy within 30.0s" while the log showed `Application startup complete`
and `Uvicorn running on ...` for both. The server had started; the health
check simply had not caught up, and the timeout then terminated it — so
the next attempt paid the whole cold start again.
"""

import inspect

import pytest

from airas.dashboard import launcher


class FakeProcess:
    def __init__(self, pid: int = 4242, returncode: int | None = None):
        self.pid = pid
        self.returncode = returncode
        self.terminated = False

    def poll(self):
        return self.returncode

    def terminate(self):
        self.terminated = True


@pytest.fixture
def spawned(monkeypatch, tmp_path):
    process = FakeProcess()
    monkeypatch.setattr(launcher, "STATE_DIR", tmp_path)
    monkeypatch.setattr(launcher, "PID_FILE", tmp_path / "dashboard.json")
    monkeypatch.setattr(launcher, "LOG_FILE", tmp_path / "dashboard.log")
    monkeypatch.setattr(launcher.subprocess, "Popen", lambda *a, **k: process)
    monkeypatch.setattr(launcher.time, "sleep", lambda _: None)
    return process


def test_a_process_that_is_still_starting_is_left_alone(spawned, monkeypatch):
    monkeypatch.setattr(launcher, "is_dashboard_running", lambda port: False)

    with pytest.raises(RuntimeError, match="still starting"):
        launcher.start_dashboard(port=24727, timeout=0.01)

    assert not spawned.terminated
    # The pid file survives, so the next call finds this process instead of
    # spawning a second one.
    assert launcher.PID_FILE.is_file()


def test_a_process_that_died_is_cleaned_up(spawned, monkeypatch):
    spawned.returncode = 1
    monkeypatch.setattr(launcher, "is_dashboard_running", lambda port: False)

    with pytest.raises(RuntimeError, match="exited with code 1"):
        launcher.start_dashboard(port=24727, timeout=0.01)

    assert not launcher.PID_FILE.is_file()


def test_a_healthy_start_returns_the_pid(spawned, monkeypatch):
    monkeypatch.setattr(launcher, "is_dashboard_running", lambda port: True)

    assert launcher.start_dashboard(port=24727, timeout=0.01) == spawned.pid


def test_the_wait_is_long_enough_for_a_cold_start():
    default = inspect.signature(launcher.start_dashboard).parameters["timeout"].default

    assert default >= 60, "30s was not enough for an observed cold start"
