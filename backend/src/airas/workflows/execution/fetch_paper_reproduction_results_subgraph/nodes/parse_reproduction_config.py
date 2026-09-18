"""Parse the generated Hydra run config into parameter entries for cross-checking.

result.json no longer carries a `parameters` field — the plain (non-tuning) run has no CLI
overrides, so its `parameters` always duplicated config/run/reproduction.yaml exactly. The
code-generation agent instead annotates each value with a `# source: ..., note: ...` comment right
in the config (see run_paper_reproduction.md in airas-template); this module is the sole place that
reads it back out.
"""

from __future__ import annotations

import re
from typing import Any

# pyyaml is a transitive dependency (via langgraph et al.), not declared directly in pyproject.toml —
# adding it explicitly pulled in unrelated fastapi/openai downgrades, so it was left transitive.
import yaml

_EXCLUDED_KEYS = {"run_id", "optuna"}
_ANNOTATED_LINE_RE = re.compile(
    r"^(?P<key>[A-Za-z_][A-Za-z0-9_]*)\s*:.*?#\s*source:\s*(?P<source>[^,]+?)"
    r"(?:,\s*note:\s*(?P<note>.+?))?\s*$"
)


def parse_reproduction_config(config_yaml: str | None) -> list[dict[str, Any]]:
    if not config_yaml:
        return []
    try:
        data = yaml.safe_load(config_yaml)
    except yaml.YAMLError:
        return []
    if not isinstance(data, dict):
        return []

    annotations: dict[str, dict[str, str | None]] = {}
    for line in config_yaml.splitlines():
        m = _ANNOTATED_LINE_RE.match(line)
        if m:
            annotations[m.group("key")] = {
                "source": m.group("source").strip(),
                "note": m.group("note").strip() if m.group("note") else None,
            }

    entries: list[dict[str, Any]] = []
    for key, value in data.items():
        if key in _EXCLUDED_KEYS:
            continue
        meta = annotations.get(key, {})
        entries.append(
            {
                "name": key,
                "value": value,
                "source": meta.get("source"),
                "note": meta.get("note"),
            }
        )
    return entries
