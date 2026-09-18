"""One tick of `airas loop`, the unattended research loop.

A tick is what a scheduler (cron, a GitHub Actions schedule, ...) calls
every few minutes. It decides without an LLM whether the active research
can move — not while a run executes, not once the paper of record exists,
not while a human has to decide — and only then resumes the agent's
conversation in the clone for one more stretch. Every decision it needs is
in the repository or in the queue issue, so it works from a fresh machine.
"""

from __future__ import annotations

import json
import re
import subprocess
from collections.abc import Iterable
from datetime import datetime, timezone
from fnmatch import fnmatch
from pathlib import Path

from airas.agent_session.agent_state import load_agent_state, restore_claude_session
from airas.core.research_paths import LOOP_PATH
from airas.infra.local_git import remote_origin_url

QUEUED, ACTIVE, PARKED, DONE = (
    "research/queued",
    "research/active",
    "research/parked",
    "research/done",
)
_REPO_LINE = re.compile(r"^repo: (\S+)", re.MULTILINE)

CONTINUE_PROMPT = (
    "Continue the AIRAS research in this clone: follow the auto-research "
    "skill's 'Resuming mid-flow' to find where it stands, then its 'Running "
    "unattended' rules. Nobody is watching: never ask a question, take the "
    "operational choices from the policy below, and stop by writing "
    ".research/loop.json when a run has to finish first or a human has to "
    "decide.\n\n{policy}"
)

START_PROMPT = (
    "Start an AIRAS research with the auto-research skill, unattended: the "
    "issue below gives the topic, the policy below gives the operational "
    "choices that 'Settle once, up front' would otherwise ask for. Never ask a "
    "question; follow the skill's 'Running unattended' rules. Create the "
    "repository under owner {owner} as research-{number}-<short-slug> and "
    "clone it into exactly {clone}.\n\n{policy}\n\n# {title}\n\n{body}"
)


def decide(
    local_path: Path, main_tree: Iterable[str], now: datetime | None = None
) -> str:
    """'done', 'parked', 'waiting' or 'advance'. `main_tree` lists the paths
    on the protected branch: only a paper of record that has landed there
    counts as done, not one in the working tree or on the staging ref."""
    if any(fnmatch(p, ".research/latex/*/paper.pdf") for p in main_tree):
        return "done"
    loop_file = local_path / LOOP_PATH
    if not loop_file.exists():
        return "advance"
    loop = json.loads(loop_file.read_text())
    if loop.get("state") == "parked":
        return "parked"
    until = loop.get("until")
    if loop.get("state") == "waiting" and until:
        deadline = datetime.fromisoformat(until.replace("Z", "+00:00"))
        if deadline.tzinfo is None:
            deadline = deadline.replace(tzinfo=timezone.utc)
        if (now or datetime.now(timezone.utc)) < deadline:
            return "waiting"
    return "advance"


def _gh(*args: str) -> str:
    return subprocess.run(
        ["gh", *args], check=True, capture_output=True, text=True
    ).stdout


def _issues(queue_repo: str, label: str) -> list[dict]:
    out = _gh(
        "issue",
        "list",
        "--repo",
        queue_repo,
        "--label",
        label,
        "--state",
        "open",
        "--json",
        "number,title,body",
        "--search",
        "sort:created-asc",
    )
    return list(json.loads(out))


def _relabel(queue_repo: str, number: int, old: str, new: str) -> None:
    _gh(
        "issue",
        "edit",
        str(number),
        "--repo",
        queue_repo,
        "--remove-label",
        old,
        "--add-label",
        new,
    )


def _park(queue_repo: str, number: int, reason: str) -> None:
    _relabel(queue_repo, number, ACTIVE, PARKED)
    _gh(
        "issue",
        "comment",
        str(number),
        "--repo",
        queue_repo,
        "--body",
        f"parked {reason}\n\nTo resume: remove `{LOOP_PATH}` in the repository "
        f"if present, then relabel `{PARKED}` → `{ACTIVE}`.",
    )


def _claude(
    prompt: str,
    cwd: Path,
    plugin_dir: str | None,
    max_turns: int,
    resume: str | None = None,
) -> None:
    cmd = [
        "claude",
        "-p",
        prompt,
        "--dangerously-skip-permissions",
        "--max-turns",
        str(max_turns),
    ]
    if plugin_dir:
        cmd += ["--plugin-dir", plugin_dir]
    if resume:
        cmd += ["--resume", resume]
    subprocess.run(cmd, cwd=cwd, check=False)


def _git(cwd: Path, *args: str, check: bool = True) -> subprocess.CompletedProcess:
    return subprocess.run(["git", "-C", str(cwd), *args], check=check)


def loop(
    queue_repo: str,
    workdir: str,
    owner: str,
    plugin_dir: str | None,
    max_turns: int,
    policy_file: str,
) -> str:
    """Advance the active research by one stretch, or start the next one.
    Returns a one-word outcome for the log."""
    policy = Path(policy_file).read_text()
    if "<fill in>" in policy:
        raise SystemExit(f"{policy_file} still has '<fill in>' placeholders")
    work = Path(workdir).expanduser().resolve()
    clone = work / "repo"
    clone.parent.mkdir(parents=True, exist_ok=True)

    active = _issues(queue_repo, ACTIVE)
    if not active:
        queued = _issues(queue_repo, QUEUED)
        if not queued:
            return "queue empty"
        issue = queued[0]
        _relabel(queue_repo, issue["number"], QUEUED, ACTIVE)
        _claude(
            START_PROMPT.format(
                owner=owner,
                number=issue["number"],
                clone=clone,
                policy=policy,
                title=issue["title"],
                body=issue["body"],
            ),
            cwd=work,
            plugin_dir=plugin_dir,
            max_turns=max_turns,
        )
        url = remote_origin_url(clone) if clone.exists() else None
        if not url:
            _park(queue_repo, issue["number"], "the first session left no clone")
            return "start failed: no clone"
        _gh(
            "issue",
            "edit",
            str(issue["number"]),
            "--repo",
            queue_repo,
            "--body",
            f"repo: {url}\n\n{issue['body']}",
        )
        _git(clone, "push", "origin", "main:verify")
        return f"started {url}"

    issue = active[0]
    match = _REPO_LINE.search(issue["body"] or "")
    if not match:
        return "active issue has no 'repo:' line"
    url = match.group(1)
    if not clone.exists():
        _git(work, "clone", url, str(clone))
    # The newest fork point may sit on the staging ref, not yet on main.
    if _git(clone, "fetch", "origin", "verify", check=False).returncode == 0:
        _git(clone, "merge", "--ff-only", "FETCH_HEAD", check=False)

    main_tree = subprocess.run(
        ["git", "-C", str(clone), "ls-tree", "-r", "--name-only", "origin/main"],
        check=True,
        capture_output=True,
        text=True,
    ).stdout.splitlines()
    outcome = decide(clone, main_tree)
    if outcome == "done":
        _relabel(queue_repo, issue["number"], ACTIVE, DONE)
        _gh("issue", "close", str(issue["number"]), "--repo", queue_repo)
    elif outcome == "parked":
        reason = json.loads((clone / LOOP_PATH).read_text()).get("reason", "")
        _park(queue_repo, issue["number"], f"by the agent: {reason}")
    elif outcome == "advance":
        try:
            state, _ = load_agent_state(str(clone))
            session_id: str | None = restore_claude_session(str(clone), state)[0]
        except FileNotFoundError:
            session_id = None
        _claude(
            CONTINUE_PROMPT.format(policy=policy),
            cwd=clone,
            plugin_dir=plugin_dir,
            max_turns=max_turns,
            resume=session_id,
        )
        # A failed push must fail the tick: on a fresh machine the fork
        # points would otherwise be lost with the clone.
        _git(clone, "push", "origin", "main:verify")
    return outcome
