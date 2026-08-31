"""Charts whose data points can only come from measured metrics.

A publication chart's Vega-Lite spec must not carry literal numbers in
its data: every numeric datum is written as a reference string
("metric:<run_id>.<path>") and resolved against the run outputs by this
module. The unresolved spec is stored next to the rendered file as a
sidecar (<file>.chartspec.json); verification re-resolves and re-renders
it and byte-compares — vl-convert is deterministic for a fixed version —
so both an edited data point and a wholesale replacement of the rendered
file surface as a mismatch, and a chart file with no sidecar is treated
as unregistered.

What stays free-form (axis titles, legends, colors) shapes presentation,
not the numbers, and is review's job — the same split as table captions.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import vl_convert as vlc

METRIC_REF_PREFIX = "metric:"
CHART_DIR = ".research/results/chart"
CHART_SPEC_SUFFIX = ".chartspec.json"
CHART_SUFFIXES = (".pdf", ".svg", ".png")


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
                        "declare it via compute_paper_values instead."
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
    """Render a resolved spec with vl-convert (deterministic per version)."""
    if suffix == "pdf":
        return vlc.vegalite_to_pdf(resolved_spec)
    if suffix == "svg":
        svg: str = vlc.vegalite_to_svg(resolved_spec)
        return svg.encode("utf-8")
    return vlc.vegalite_to_png(resolved_spec)


def renderer_version() -> str:
    version = getattr(vlc, "__version__", "unknown")
    return f"vl-convert-python {version}"


def write_chart_sidecar(chart_path: Path, spec: Any, suffix: str) -> Path:
    sidecar_path = chart_path.with_name(chart_path.name + CHART_SPEC_SUFFIX)
    sidecar_path.write_text(
        json.dumps(
            {"spec": spec, "format": suffix, "renderer": renderer_version()},
            indent=2,
            ensure_ascii=False,
        )
        + "\n",
        encoding="utf-8",
    )
    return sidecar_path


def verify_charts(local_repo_path: str, metrics_data: dict[str, Any]) -> list[str]:
    """Re-render every registered chart and report what does not hold up.

    Returned strings are mismatch descriptions (empty = all charts check
    out). A chart file without a sidecar is unregistered — its data has
    no declared source — and a sidecar whose re-render differs from the
    committed bytes means the data, the spec, or the file was changed
    after rendering.
    """
    chart_dir = Path(local_repo_path).expanduser().resolve() / CHART_DIR
    if not chart_dir.is_dir():
        return []

    problems: list[str] = []
    for chart_path in sorted(chart_dir.iterdir()):
        if chart_path.suffix.lower() not in CHART_SUFFIXES:
            continue
        relative = f"{CHART_DIR}/{chart_path.name}"
        sidecar_path = chart_path.with_name(chart_path.name + CHART_SPEC_SUFFIX)
        if not sidecar_path.is_file():
            problems.append(
                f"{relative}: no {CHART_SPEC_SUFFIX} sidecar — the chart is "
                "not registered with render_chart, so its data has no "
                "declared source"
            )
            continue
        try:
            sidecar = json.loads(sidecar_path.read_text(encoding="utf-8"))
            resolved, _ = substitute_chart_refs(sidecar["spec"], metrics_data)
            expected = render_chart_bytes(resolved, sidecar["format"])
        except Exception as e:
            problems.append(f"{relative}: sidecar could not be re-rendered: {e}")
            continue
        if chart_path.read_bytes() != expected:
            recorded = sidecar.get("renderer", "unknown renderer")
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
                f"{relative}: file differs from a re-render of its declared spec{hint}"
            )
    return problems


def chart_result_dirs(local_repo_path: str, metrics_data: dict[str, Any]) -> set[str]:
    """Every results directory the registered charts draw data from."""
    from airas.usecases.publication.paper_values.compute import match_run_id

    chart_dir = Path(local_repo_path).expanduser().resolve() / CHART_DIR
    if not chart_dir.is_dir():
        return set()
    dirs: set[str] = set()
    for sidecar_path in sorted(chart_dir.glob(f"*{CHART_SPEC_SUFFIX}")):
        try:
            sidecar = json.loads(sidecar_path.read_text(encoding="utf-8"))
            _, refs = substitute_chart_refs(sidecar["spec"], metrics_data)
        except Exception:
            continue  # verify_charts reports the breakage itself
        for ref in refs:
            run_id = match_run_id(metrics_data, ref)
            if run_id is not None:
                dirs.add(run_id)
    return dirs
