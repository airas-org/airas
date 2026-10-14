from __future__ import annotations

import re
from typing import Any

from airas.core.types.research_record import ResearchRecord

_ENTRY_ID_KEYS = {
    "literature": "id",
    "repositories": "id",
    "passages": "id",
    "hypotheses": "id",
    "claims": "id",
    "designs": "id",
    "runs": "run_id",
    "results": "id",
    "tables": "key",
    "charts": "path",
}
_COMPARED_AS_ONE_VALUE = frozenset(
    {
        "criterion",
        "prediction",
        "verifier",
        "metrics",
        "eval_inputs",
        "eval_report",
        "fulltext",
        "snapshot",
        "spec",
        "quoted_passage_ids",
        "extension_points",
        "arguments",
    }
)
_WRITTEN_BY_JUDGES = frozenset({"reviews", "judgments"})


def _entries(key: str, items: list[Any]) -> list[tuple[str, Any]]:
    id_key = _ENTRY_ID_KEYS.get(key)
    if id_key is not None and all(isinstance(i, dict) and id_key in i for i in items):
        live = {str(i[id_key]): i for i in items}
        return [
            (f"{key}[{entry_id}]", {k: v for k, v in i.items() if k != id_key})
            for entry_id, i in live.items()
        ]
    return [(f"{key}[{n}]", i) for n, i in enumerate(items)]


def _walk(prefix: str, key: str, value: Any, out: dict[str, Any]) -> None:
    path = f"{prefix}/{key}" if prefix else key
    if key in _WRITTEN_BY_JUDGES:
        return
    if key in _COMPARED_AS_ONE_VALUE or not isinstance(value, (dict, list)):
        out[path] = value
        return
    if isinstance(value, dict):
        for child_key, child in value.items():
            _walk(path, child_key, child, out)
        return
    for segment, item in _entries(key, value):
        child_path = f"{prefix}/{segment}" if prefix else segment
        if isinstance(item, dict):
            for child_key, child in item.items():
                _walk(child_path, child_key, child, out)
        else:
            out[child_path] = item


def declaration_paths(record: ResearchRecord) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for key, value in record.model_dump(exclude_defaults=True).items():
        _walk("", key, value, out)
    return out


def _json_lines(node: Any) -> int:
    """Lines `node` takes as record.save writes it (indent=2)."""
    items = list(node.values()) if isinstance(node, dict) else node
    if not isinstance(items, list):
        return 1
    return 2 + sum(_json_lines(item) for item in items) if items else 1


def line_at(data: Any, index_path: list[Any]) -> int | None:
    """1-based line of record.json holding the node at `index_path`, or None. ponytail:
    counts the layout record.save writes; a hand-formatted record gets no line."""
    node, line = data, 1
    try:
        for key in index_path:
            items = list(node.values()) if isinstance(node, dict) else node
            index = list(node).index(key) if isinstance(node, dict) else int(key)
            line += 1 + sum(_json_lines(item) for item in items[:index])
            node = items[index]
    except (ValueError, IndexError, TypeError):
        return None
    return line


def record_json_line(data: Any, path: str) -> int | None:
    """Line of record.json holding the declaration at an id-addressed `path`."""
    node, index_path = data, []
    for segment in path.split("/"):
        match = re.fullmatch(r"([^\[]+)\[(.+)\]", segment)
        key, entry = (match.group(1), match.group(2)) if match else (segment, None)
        if not isinstance(node, dict) or key not in node:
            return None
        index_path.append(key)
        node = node[key]
        if entry is None:
            continue
        if not isinstance(node, list):
            return None
        id_key = _ENTRY_ID_KEYS.get(key)
        if id_key is None:
            index = int(entry) if entry.isdigit() else -1
        else:
            same_id = [
                n
                for n, item in enumerate(node)
                if isinstance(item, dict) and str(item.get(id_key)) == entry
            ]
            index = same_id[-1] if same_id else -1
        if not 0 <= index < len(node):
            return None
        index_path.append(index)
        node = node[index]
    return line_at(data, index_path)
