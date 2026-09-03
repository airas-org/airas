from __future__ import annotations

from pathlib import Path
from typing import Any

import vl_convert as vlc

from airas.core.types.research_record import ResearchRecord

METRIC_REF_PREFIX = "metric:"
CHART_DIR = ".research/results/chart"
# Every chart-like file under CHART_DIR is scanned (a smuggled PDF must
# not escape), but only svg and png can actually be verified: vl-convert's
# PDF writer emits hash-ordered dictionaries, so PDF bytes differ across
# processes even for identical input and can never match a re-render.
CHART_SUFFIXES = (".pdf", ".svg", ".png")
# Fixed render scale for png charts: part of the deterministic contract,
# and high enough for print.
PNG_SCALE = 3.0


def substitute_chart_refs(
    spec: Any, metrics_data: dict[str, Any]
) -> tuple[Any, set[str]]:
    """Resolve every metric reference in a spec; reject literal data numbers.

    Only the datum objects (entries under any "values" list of a "data" or
    "datasets" mapping) are constrained — sizes, scales and axis domains
    elsewhere in the spec are presentation, not claims. Returns the
    resolved spec and the refs that were used.
    """
    from airas.usecases.publication.paper_values.compute import resolve_ref

    refs_used: set[str] = set()

    def resolve_datum_field(value: Any, context: str) -> Any:
        if isinstance(value, str) and value.startswith(METRIC_REF_PREFIX):
            ref = value[len(METRIC_REF_PREFIX) :]
            refs_used.add(ref)
            return resolve_ref(metrics_data, ref)
        if isinstance(value, bool) or value is None or isinstance(value, str):
            return value
        if isinstance(value, (int, float)):
            raise ValueError(
                f"literal number {value!r} in {context}: chart data must "
                f"reference measured metrics as "
                f"'{METRIC_REF_PREFIX}<run_id>.<path>' so the plotted "
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
                        "declare it via update_and_verify_record instead."
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


def render_chart_bytes(resolved_spec: dict[str, Any], suffix: str) -> bytes:
    if suffix == "svg":
        svg: str = vlc.vegalite_to_svg(resolved_spec)
        return svg.encode("utf-8")
    if suffix == "png":
        return vlc.vegalite_to_png(resolved_spec, scale=PNG_SCALE)
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


def verify_charts(
    record: ResearchRecord, local_repo_path: str, metrics_data: dict[str, Any]
) -> list[str]:
    """Re-render every declared chart; reject undeclared chart files."""
    from airas.usecases.publication.paper_values.record import active

    chart_dir = Path(local_repo_path).expanduser().resolve() / CHART_DIR
    declared = {c.path: c for c in active(record.charts, "path")}
    renderers = {c.path: c.renders[-1].renderer for c in record.charts if c.renders}

    problems: list[str] = []
    if chart_dir.is_dir():
        # Recursive: the LaTeX export collects figures from any depth under
        # .research/results/, so a chart hidden in a subdirectory must not
        # escape the declaration requirement.
        for chart_path in sorted(chart_dir.rglob("*")):
            if not chart_path.is_file():
                continue
            if chart_path.suffix.lower() not in CHART_SUFFIXES:
                continue
            relative = chart_path.relative_to(chart_dir).as_posix()
            if relative not in declared:
                problems.append(
                    f"{CHART_DIR}/{relative} is not declared in record.json — "
                    "its data has no declared source (render_chart declares "
                    "and renders in one step)"
                )

    for relative, declaration in declared.items():
        chart_path = chart_dir / relative
        if not chart_path.is_file():
            problems.append(
                f"{CHART_DIR}/{relative} is declared but missing "
                "(render_chart writes it)"
            )
            continue
        try:
            resolved, _ = substitute_chart_refs(declaration.spec, metrics_data)
            expected = render_chart_bytes(resolved, declaration.format)
        except Exception as e:
            problems.append(
                f"{CHART_DIR}/{relative}: spec could not be re-rendered: {e}"
            )
            continue
        if chart_path.read_bytes() != expected:
            recorded = renderers.get(relative, "unknown renderer")
            hint = (
                ""
                if recorded == renderer_version()
                else (
                    f" (rendered with {recorded}, verifying with "
                    f"{renderer_version()} — re-render to rule out a "
                    "renderer version difference)"
                )
            )
            problems.append(
                f"{CHART_DIR}/{relative}: file differs from a re-render of "
                f"its declared spec{hint}"
            )
    return problems


def chart_result_dirs(record: ResearchRecord, metrics_data: dict[str, Any]) -> set[str]:
    from airas.usecases.publication.paper_values.compute import match_run_id
    from airas.usecases.publication.paper_values.record import active

    dirs: set[str] = set()
    for declaration in active(record.charts, "path"):
        try:
            _, refs = substitute_chart_refs(declaration.spec, metrics_data)
        except Exception:
            continue  # verify_charts reports the breakage itself
        for ref in refs:
            run_id = match_run_id(metrics_data, ref)
            if run_id is not None:
                dirs.add(run_id)
    return dirs
