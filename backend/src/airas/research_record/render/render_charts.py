from __future__ import annotations

import copy
from typing import Any

import vl_convert as vlc

from airas.research_record.render._resolve_ref import resolve_ref

CHART_DIR = ".research/results/chart"


# Every chart-like file under CHART_DIR is scanned (a smuggled PDF must
# not escape), but only svg and png can actually be verified: vl-convert's
# PDF writer emits hash-ordered dictionaries, so PDF bytes differ across
# processes even for identical input and can never match a re-render.
CHART_SUFFIXES = (".pdf", ".svg", ".png")


def substitute_chart_refs(
    spec: Any, metrics_data: dict[str, Any]
) -> tuple[Any, set[str]]:
    refs_used: set[str] = set()

    def resolve_datum_field(value: Any, context: str) -> Any:
        if isinstance(value, str) and value.startswith("metric:"):
            ref = value[len("metric:") :]
            refs_used.add(ref)
            return resolve_ref(metrics_data, ref)
        if isinstance(value, bool) or value is None or isinstance(value, str):
            return value
        if isinstance(value, (int, float)):
            raise ValueError(
                f"literal number {value!r} in {context}: chart data must "
                f"reference measured metrics as "
                f"'metric:<run_id>.<path>' so the plotted "
                "points cannot be invented"
            )
        raise ValueError(f"unsupported datum value {value!r} in {context}")

    def resolve_datum(datum: Any, context: str) -> Any:
        if isinstance(datum, dict):
            return {
                field: resolve_datum_field(value, f"{context}.{field}")
                for field, value in datum.items()
            }
        return resolve_datum_field(datum, context)

    def walk(node: Any, in_data: bool) -> Any:
        # `in_data` marks the dict under a "data" or "datasets" key: any
        # list there ("values", or a named inline dataset) is datum rows.
        if isinstance(node, dict):
            for forbidden in ("calculate", "expr"):
                if forbidden in node:
                    raise ValueError(
                        f"'{forbidden}' is not allowed in a chart spec: an "
                        "expression can turn measured points into invented "
                        "ones. Derive the value in the experiment code or "
                        "declare it via update_record instead."
                    )
            return {
                key: (
                    [
                        resolve_datum(datum, f"{key}[{i}]")
                        for i, datum in enumerate(value)
                    ]
                    if in_data and isinstance(value, list)
                    else walk(value, key in ("data", "datasets"))
                )
                for key, value in node.items()
            }
        if isinstance(node, list):
            # A list outside data (layer, hconcat, transform, ...): sub-specs.
            return [walk(item, False) for item in node]
        return node

    return walk(spec, False), refs_used


# Zero-based marks on a bounded axis are clipped.
_ZERO_BASED_MARKS = frozenset({"bar", "area", "rect"})


def _mark_type(mark: Any) -> str | None:
    if isinstance(mark, str):
        return mark
    if isinstance(mark, dict):
        kind = mark.get("type")
        return kind if isinstance(kind, str) else None
    return None


def _has_explicit_domain(encoding: Any) -> bool:
    if not isinstance(encoding, dict):
        return False
    for channel in ("x", "y"):
        scale = (
            encoding.get(channel, {}).get("scale")
            if isinstance(encoding.get(channel), dict)
            else None
        )
        if isinstance(scale, dict) and scale.get("domain") is not None:
            return True
    return False


def _clip_view(view: dict[str, Any], inherited_encoding: dict[str, Any]) -> None:
    view_encoding = view.get("encoding")
    encoding = dict(inherited_encoding)
    if isinstance(view_encoding, dict):
        encoding.update(view_encoding)
    kind = _mark_type(view.get("mark"))
    if kind in _ZERO_BASED_MARKS and _has_explicit_domain(encoding):
        mark = view["mark"]
        if isinstance(mark, str):
            mark = {"type": mark}
        mark.setdefault("clip", True)
        view["mark"] = mark
    for key in ("layer", "hconcat", "vconcat", "concat"):
        for child in view.get(key) or []:
            if isinstance(child, dict):
                _clip_view(child, encoding)
    spec = view.get("spec")
    if isinstance(spec, dict):
        _clip_view(spec, encoding)


def clip_zero_based_marks(spec: dict[str, Any]) -> dict[str, Any]:
    out = copy.deepcopy(spec)
    _clip_view(out, {})
    return out


def render_chart_bytes(resolved_spec: dict[str, Any], suffix: str) -> bytes:
    if suffix == "svg":
        svg: str = vlc.vegalite_to_svg(resolved_spec)
        return svg.encode("utf-8")
    if suffix == "png":
        # Fixed scale: part of the deterministic contract, high enough for print.
        return vlc.vegalite_to_png(resolved_spec, scale=3.0)
    if suffix == "pdf":
        raise ValueError(
            "pdf charts cannot be verified: vl-convert's PDF output is not "
            "byte-deterministic across processes, so a re-render never "
            "matches. Render the chart as png (LaTeX includes it directly)."
        )
    raise ValueError(f"unsupported chart format {suffix!r} (expected 'svg' or 'png')")


def renderer_version() -> str:
    version = getattr(vlc, "__version__", "unknown")
    return f"vl-convert-python {version}"
