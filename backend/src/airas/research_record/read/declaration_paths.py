from __future__ import annotations

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
    "arguments": "argument",
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
