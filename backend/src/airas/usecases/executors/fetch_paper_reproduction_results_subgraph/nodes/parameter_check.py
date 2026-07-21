"""Deterministic (non-LLM) cross-check of self-reported parameters against paper-extracted values.

The reported parameters (parsed from config/run/reproduction.yaml — see parse_reproduction_config.py)
and paper_extraction["parameters"] (values a separate, later agent process independently extracted
from the paper, given only the parameter key schema — see paper_extraction.json) are expected to
share key names, so the cross-check reduces to a name lookup and a tolerant value comparison — no
fuzzy name matching needed.

`source` and `note` are carried through as context for the judge LLM: `source` is the
code-generation agent's own declaration of where the value came from (`paper` / `assumed` /
`paper_unspecified` / `substituted`), and `note` is a free-text justification (e.g. which
section/table the value was read from) that the agent records as a config comment alongside the
value.
"""

from __future__ import annotations

import re
from typing import Any

_NUMERIC_TOLERANCE = 0.05


def normalize_key(name: str) -> str:
    normalized = re.sub(r"[\s\-]+", "_", str(name).strip().lower())
    return re.sub(r"_+", "_", normalized).strip("_")


def values_match(reported_value: Any, paper_value: Any) -> bool:
    a, b = str(reported_value).strip(), str(paper_value).strip()
    try:
        fa, fb = float(a), float(b)
    except ValueError:
        a_norm = re.sub(r"[^a-z0-9]", "", a.lower())
        b_norm = re.sub(r"[^a-z0-9]", "", b.lower())
        return bool(a_norm) and a_norm == b_norm
    if fb == 0:
        return fa == fb
    return abs(fa - fb) / abs(fb) <= _NUMERIC_TOLERANCE


def cross_check_parameters(
    reported_params: list[dict], paper_params: list[dict]
) -> dict[str, list[dict]]:
    if not isinstance(
        reported_params, list
    ):  # result.json is agent-authored, not schema-validated
        reported_params = []
    if not isinstance(paper_params, list):
        paper_params = []

    paper_by_key: dict[str, Any] = {}
    paper_raw_name: dict[str, str] = {}
    for p in paper_params:
        if not isinstance(
            p, dict
        ):  # result.json is agent-authored, not schema-validated
            continue
        key = normalize_key(p.get("name", ""))
        if (
            key and key not in paper_by_key
        ):  # duplicate keys aren't expected; keep the first
            paper_by_key[key] = p.get("value")
            paper_raw_name[key] = str(p.get("name", "")).strip()

    matched: list[dict] = []
    mismatched: list[dict] = []
    unverifiable: list[dict] = []

    for p in reported_params:
        if not isinstance(p, dict):
            continue
        raw_name = str(p.get("name", "")).strip()
        key = normalize_key(raw_name)
        if not key:
            continue
        reported_value = p.get("value")
        source = p.get("source") or None
        note = p.get("note") or None

        if key not in paper_by_key:
            unverifiable.append(
                {
                    "name": raw_name,
                    "reported_value": reported_value,
                    "paper_value": None,
                    "source": source,
                    "note": note,
                }
            )
            continue

        paper_value = paper_by_key[key]
        entry = {
            "name": raw_name,
            "reported_value": reported_value,
            "paper_value": paper_value,
            "source": source,
            "note": note,
        }
        (matched if values_match(reported_value, paper_value) else mismatched).append(
            entry
        )

    return {"matched": matched, "mismatched": mismatched, "unverifiable": unverifiable}


def format_evidence(check: dict[str, list[dict]]) -> str:
    lines = [
        "## Parameter cross-check (pre-computed deterministically — do not repeat this judgment)"
    ]
    if not any(check.values()):
        lines.append("- (no parameters could be extracted from either side)")
        return "\n".join(lines)
    for p in check["matched"]:
        note_suffix = f", note={p['note']}" if p["note"] else ""
        lines.append(
            f"- match: {p['name']} (source={p['source'] or 'unknown'}{note_suffix})"
        )
    for p in check["mismatched"]:
        note_suffix = f", note={p['note']}" if p["note"] else ""
        lines.append(
            f"- MISMATCH: {p['name']} (reported={p['reported_value']}, paper={p['paper_value']}, "
            f"source={p['source'] or 'unknown'}{note_suffix})"
        )
    for p in check["unverifiable"]:
        note_suffix = f", note={p['note']}" if p["note"] else ""
        lines.append(
            f"- unverifiable (no matching paper entry): {p['name']} "
            f"(reported={p['reported_value']}, source={p['source'] or 'unknown'}{note_suffix})"
        )
    return "\n".join(lines)
