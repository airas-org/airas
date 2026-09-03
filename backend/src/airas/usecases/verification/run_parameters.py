"""What a run was dispatched with, read from the platform's own record.

Shared by the import step (which caches these into `.provenance.json`) and
the verifier (which re-derives them from Seyval and compares against that
cache), so both sides parse the platform's report the same way. Two
parsers would have to agree forever, and the day they disagreed every
honest cache would read as a forgery.
"""

from __future__ import annotations

from typing import Any


def parse_overrides(command_args: Any) -> dict[str, str]:
    """The dispatch's parameter overrides, from the argv Seyval recorded.

    Only `key=value` tokens are overrides; the rest of the argv is the
    interpreter and module path. Hydra's `+key=` / `~key=` prefixes are
    stripped so a declaration can be compared against what ran without
    knowing which form the dispatch used.
    """
    overrides: dict[str, str] = {}
    for token in command_args or []:
        text = str(token)
        key, separator, value = text.partition("=")
        if not separator or key.startswith("-") or "/" in key:
            continue
        overrides[key.strip().lstrip("+~")] = value.strip()
    return overrides


def parse_parameters(run: Any) -> dict[str, str]:
    """Every parameter the run resolved, as Seyval reports it.

    Strictly better than the argv-derived overrides: those carry only what
    the dispatch restated, so a parameter left at its default is
    indistinguishable from one that was never reported. Absent until the
    platform supplies it, in which case callers fall back to the overrides
    and treat a missing key as unknown rather than as a default.
    """
    reported = run.get("resolved_parameters") or run.get("parameters")
    if isinstance(reported, dict):
        return {str(k): str(v) for k, v in reported.items()}
    # The list form the run schema uses: [{"name": ..., "value": ...}, ...]
    if isinstance(reported, list):
        return {
            str(entry["name"]): str(entry.get("value"))
            for entry in reported
            if isinstance(entry, dict) and entry.get("name")
        }
    return {}
