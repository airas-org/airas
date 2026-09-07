"""Install the SessionStart hook for Codex CLI.

Codex has no plugin that carries hooks, so the hook is written to the
user's `~/.codex/hooks.json` (effective in every project) and the hooks
feature is switched on in `~/.codex/config.toml`.
"""

from __future__ import annotations

import json
from pathlib import Path

import tomli
import tomli_w

from airas.usecases.recording.agent_state import CODEX_HOME

SESSION_START_COMMAND = "uvx --with 'mcp<2' airas hook session-start --harness codex"


def install_codex_hooks(home: Path = CODEX_HOME) -> str:
    home.mkdir(parents=True, exist_ok=True)
    hooks_path = home / "hooks.json"
    hooks = json.loads(hooks_path.read_text()) if hooks_path.is_file() else {}
    groups = hooks.setdefault("hooks", {}).setdefault("SessionStart", [])
    if not any(
        h.get("command") == SESSION_START_COMMAND
        for group in groups
        for h in group.get("hooks", [])
    ):
        groups.append(
            {"hooks": [{"type": "command", "command": SESSION_START_COMMAND}]}
        )
    hooks_path.write_text(json.dumps(hooks, indent=2) + "\n")

    config_path = home / "config.toml"
    config = tomli.loads(config_path.read_text()) if config_path.is_file() else {}
    config.setdefault("features", {})["codex_hooks"] = True
    config_path.write_text(tomli_w.dumps(config))
    return f"installed SessionStart hook in {hooks_path}; enabled features.codex_hooks in {config_path}"
