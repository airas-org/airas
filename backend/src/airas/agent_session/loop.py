"""`airas loop`: 研究 1 本ぶんの agent セッションを起こす。resume 先の URL が
あれば前回の会話を復元して続きを、なければ新しい研究を始める。"""

from __future__ import annotations

import subprocess
from pathlib import Path

from airas.agent_session.agent_state import load_agent_state, restore_claude_session
from airas.infra.local_git import remote_origin_url

CONTINUE_PROMPT = (
    "Continue the AIRAS research in this clone: follow the auto-research "
    "skill's 'Resuming mid-flow' to find where it stands, then its 'Running "
    "unattended' rules. Nobody is watching: never ask a question, take the "
    "operational choices from the policy below.\n\n{policy}"
)

START_PROMPT = (
    "Start a new AIRAS research with the auto-research skill, unattended: "
    "choose the topic within the research area of the policy below, building "
    "on the AIRAS research already in the paper store, and take the "
    "operational choices from the same policy. Never ask a question; follow "
    "the skill's 'Running unattended' rules. Create the repository under owner "
    "{owner} as research-<short-slug> and clone it into exactly {clone}.\n\n"
    "{policy}"
)


def loop(
    resume_repo: str, workdir: str, owner: str, plugin_dir: str | None, policy_file: str
) -> None:
    policy = Path(policy_file).read_text()
    if "<fill in>" in policy:
        raise SystemExit(f"{policy_file} still has '<fill in>' placeholders")
    work = Path(workdir).expanduser().resolve()
    # 新規でも agent にここへ clone させる。job が殺されても最終 step が URL を拾えるように場所を固定する
    clone = work / "repo"
    work.mkdir(parents=True, exist_ok=True)

    cmd = ["claude", "-p", "--dangerously-skip-permissions"]
    if plugin_dir:
        cmd += ["--plugin-dir", plugin_dir]
    if resume_repo:
        subprocess.run(["git", "clone", resume_repo, str(clone)], check=True)
        # 最新の fork point は staging ref(verify)にいることがある
        subprocess.run(
            ["git", "-C", str(clone), "fetch", "origin", "verify"], check=False
        )
        subprocess.run(
            ["git", "-C", str(clone), "merge", "--ff-only", "FETCH_HEAD"], check=False
        )
        state, _ = load_agent_state(str(clone))
        session_id, _ = restore_claude_session(str(clone), state)
        cmd += ["--resume", session_id, CONTINUE_PROMPT.format(policy=policy)]
        result = subprocess.run(cmd, cwd=clone, check=False)
    else:
        cmd.append(START_PROMPT.format(owner=owner, clone=clone, policy=policy))
        result = subprocess.run(cmd, cwd=work, check=False)
    # 人待ちで archive されたリポは失敗として返し、workflow が次の研究を即座に始めないようにする
    if result.returncode == 0 and clone.exists() and _archived(clone):
        raise SystemExit(1)
    # claude の終了コードをそのまま返し、workflow が失敗を見分けられるようにする
    raise SystemExit(result.returncode)


def _archived(clone: Path) -> bool:
    url = remote_origin_url(clone)
    if not url:
        return False
    out = subprocess.run(
        ["gh", "repo", "view", url, "--json", "isArchived", "-q", ".isArchived"],
        capture_output=True,
        text=True,
        check=False,
    ).stdout.strip()
    return out == "true"
