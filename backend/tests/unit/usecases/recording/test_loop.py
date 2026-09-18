from datetime import datetime, timedelta, timezone
from pathlib import Path

from airas.agent_session.loop import decide
from airas.core.research_paths import LOOP_PATH


def _loop(tmp_path: Path, body: str) -> None:
    path = tmp_path / LOOP_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(body)


def test_decide_reads_the_clone_and_the_protected_branch(tmp_path: Path) -> None:
    now = datetime(2026, 9, 18, 12, 0, tzinfo=timezone.utc)
    assert decide(tmp_path, [], now) == "advance"

    _loop(tmp_path, '{"state": "parked", "reason": "two identical failures"}')
    assert decide(tmp_path, [], now) == "parked"

    later = (now + timedelta(hours=3)).isoformat()
    _loop(tmp_path, f'{{"state": "waiting", "until": "{later}"}}')
    assert decide(tmp_path, [], now) == "waiting"
    assert decide(tmp_path, [], now + timedelta(hours=4)) == "advance"

    # An offset-less or Z-suffixed timestamp is read as UTC, not a TypeError.
    _loop(tmp_path, '{"state": "waiting", "until": "2026-09-18T15:00:00"}')
    assert decide(tmp_path, [], now) == "waiting"
    _loop(tmp_path, '{"state": "waiting", "until": "2026-09-18T15:00:00Z"}')
    assert decide(tmp_path, [], now) == "waiting"

    # Only the paper of record on the protected branch counts as done.
    pdf = tmp_path / ".research/latex/mdpi/paper.pdf"
    pdf.parent.mkdir(parents=True)
    pdf.write_bytes(b"%PDF")
    assert decide(tmp_path, [".research/record.json"], now) == "waiting"
    assert decide(tmp_path, [".research/latex/mdpi/paper.pdf"], now) == "done"
