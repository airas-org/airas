"""Manage the dashboard server as a detached background process.

Used by the MCP server's `open_dashboard` / `stop_dashboard` tools. The
dashboard is spawned as a separate process group so it keeps serving after
the MCP server (and the MCP client that launched it) exits.
"""

import json
import os
import signal
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

import httpx

STATE_DIR = Path("~/.airas").expanduser()
PID_FILE = STATE_DIR / "dashboard.json"
LOG_FILE = STATE_DIR / "dashboard.log"


def dashboard_url(port: int) -> str:
    return f"http://localhost:{port}"


def is_dashboard_running(port: int) -> bool:
    """True if an AIRAS dashboard answers on the port."""
    try:
        resp = httpx.get(f"http://127.0.0.1:{port}/health", timeout=2.0)
        return resp.status_code == 200 and resp.json().get("status") == "ok"
    except Exception:
        return False


def has_bundled_ui() -> bool:
    """True if this installation ships the built web frontend."""
    import airas.dashboard

    static_dir = Path(airas.dashboard.__file__).resolve().parent / "static"
    return (static_dir / "index.html").is_file()


def start_dashboard(port: int, timeout: float = 30.0) -> int:
    """Spawn `airas dashboard` in the background and wait until it is healthy.

    Returns the child PID. Raises RuntimeError if the process dies or does
    not become healthy in time.
    """
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    with open(LOG_FILE, "ab") as log:
        # stdout/stderr must not be inherited: the MCP server speaks its
        # protocol on stdio, and any stray output would corrupt it.
        proc = subprocess.Popen(
            [
                sys.executable,
                "-m",
                "airas.cli",
                "dashboard",
                "--no-browser",
                "--host",
                "127.0.0.1",
                "--port",
                str(port),
            ],
            stdin=subprocess.DEVNULL,
            stdout=log,
            stderr=log,
            start_new_session=True,
        )

    PID_FILE.write_text(json.dumps({"pid": proc.pid, "port": port}))

    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if is_dashboard_running(port):
            return proc.pid
        if proc.poll() is not None:
            PID_FILE.unlink(missing_ok=True)
            raise RuntimeError(
                f"Dashboard process exited with code {proc.returncode} "
                f"(is port {port} already in use?). See {LOG_FILE} for details."
            )
        time.sleep(0.3)

    proc.terminate()
    PID_FILE.unlink(missing_ok=True)
    raise RuntimeError(
        f"Dashboard did not become healthy within {timeout}s. See {LOG_FILE}."
    )


def stop_dashboard(timeout: float = 10.0) -> dict[str, Any]:
    """Stop a dashboard previously started by `start_dashboard`."""
    if not PID_FILE.is_file():
        return {
            "stopped": False,
            "reason": "No dashboard has been started via MCP on this machine.",
        }

    info = json.loads(PID_FILE.read_text())
    pid = int(info["pid"])

    try:
        os.kill(pid, signal.SIGTERM)
    except ProcessLookupError:
        PID_FILE.unlink(missing_ok=True)
        return {"stopped": False, "reason": "Dashboard process had already exited."}

    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        try:
            os.kill(pid, 0)
        except ProcessLookupError:
            break
        time.sleep(0.2)
    else:
        try:
            os.kill(pid, signal.SIGKILL)
        except ProcessLookupError:
            pass

    PID_FILE.unlink(missing_ok=True)
    return {"stopped": True, "pid": pid, "port": info.get("port")}
