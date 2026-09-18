"""Chart and diagram rendering."""

import asyncio
from pathlib import Path
from typing import Any

from airas.core.research_paths import (
    RECORD_PATH,
)
from airas.core.types.research_record import (
    ChartDeclaration,
    RenderedChart,
    active,
)
from airas.infra.local_git import commit_paths
from airas.mcp.app import mcp
from airas.mcp.context import (
    _kroki_client,
)
from airas.research_record.read.find_by_id import find_hypothesis
from airas.research_record.read.load_record import load_record, record_path
from airas.research_record.read.read_run_outputs import load_metrics_data
from airas.research_record.render.render_charts import (
    CHART_DIR,
    clip_zero_based_marks,
    render_chart_bytes,
    renderer_version,
    substitute_chart_refs,
)
from airas.usecases.publication.render_diagram import (
    render_diagram as render_diagram_usecase,
)


@mcp.tool()
async def render_chart(
    vega_lite_spec: dict[str, Any],
    output_path: str,
    local_path: str,
    hypothesis_id: str,
) -> dict[str, Any]:
    """Render a result chart whose data points come from measured metrics.

    Use this for publication-quality result figures. The Vega-Lite spec
    must not contain literal numbers in its data: write every numeric
    datum as `"metric:<run_id>.<path>"` (e.g. `"metric:run_1.accuracy"`),
    and the tool resolves it against `.research/results/` in `local_path`
    itself — so a plotted point cannot be a number no run measured.
    Categorical fields (method names, dataset labels) stay plain strings;
    `calculate`/`expr` transforms are rejected. `\\unverified` has no
    chart equivalent: a number that no run produced does not belong in a
    result figure.

    Save charts as **PNG** under `.research/results/chart/` in the clone
    (`output_path` must lie under that directory and end with .png or
    .svg), then commit and push — the LaTeX build collects figure PDFs
    and PNGs under `.research/results/`. PDF chart output is refused:
    vl-convert's PDF bytes are not deterministic across processes, so a
    PDF chart could never be verified against a re-render. The unresolved
    spec is appended to `.research/record.json`, under the hypothesis
    named by `hypothesis_id`, as the chart's declaration, and the chart and record.json are committed together in
    the same step (`commit` in the result); `verify_paper_values`
    re-resolves, re-renders and byte-compares. A path that already has a
    different declared spec is refused — render to a new path, or
    supersede the old declaration via `append_to_record`.
    Rendering runs in-process (vl-convert); no data leaves the machine
    and no API keys are required.
    """
    path = Path(output_path).expanduser()
    suffix = path.suffix.lower().lstrip(".")
    if suffix not in ("png", "svg"):
        raise ValueError(
            "output_path must end with .png or .svg: pdf charts cannot be "
            "verified (vl-convert's PDF bytes are not deterministic across "
            "processes), and LaTeX includes png directly"
        )
    chart_root = Path(local_path).expanduser().resolve() / CHART_DIR
    try:
        relative = path.relative_to(chart_root).as_posix()
    except ValueError:
        raise ValueError(
            f"output_path must be under {CHART_DIR}/ in the clone — that is "
            "the only place verified charts are collected from"
        ) from None

    def _run() -> dict[str, Any]:
        # Declared as clipped: bars drawn from zero overrun a bounded axis.
        spec = clip_zero_based_marks(vega_lite_spec)
        record = load_record(local_path)
        target = find_hypothesis(record, hypothesis_id)
        metrics_data = load_metrics_data(local_path)
        resolved, _ = substitute_chart_refs(spec, metrics_data)
        data = render_chart_bytes(resolved, suffix)

        declared = next(
            (c for c in active(target.charts, "path") if c.path == relative),
            None,
        )
        if declared and (declared.spec != spec or declared.format != suffix):
            raise ValueError(
                f"{relative} already has a different declared spec; render to "
                "a new path, or append a superseding declaration via "
                "append_to_record"
            )
        if declared is None:
            target.charts.append(
                ChartDeclaration(
                    path=relative,
                    format=suffix,
                    spec=spec,
                )
            )
        next(
            c for c in active(target.charts, "path") if c.path == relative
        ).renders.append(RenderedChart(renderer=renderer_version()))
        record.save(local_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
        commit = commit_paths(
            Path(local_path).expanduser().resolve(),
            [RECORD_PATH, f"{CHART_DIR}/{relative}"],
            f"record: declare and render chart {relative}",
        )
        return {
            "output_path": str(path),
            "bytes_written": len(data),
            "record_path": str(record_path(local_path)),
            "commit": commit,
            "note": (
                f"chart and record.json committed together; charts under "
                f"{CHART_DIR}/ are verified against a re-render of their "
                "declared spec"
            ),
        }

    return await asyncio.to_thread(_run)


@mcp.tool()
async def render_diagram(
    diagram_type: str,
    diagram_source: str,
    output_path: str,
) -> dict[str, Any]:
    """Render a text diagram (diagram-as-code) to a file via Kroki.

    Use this for method/architecture diagrams: write the diagram source in
    a text notation (`diagram_type`: "mermaid", "graphviz", "d2",
    "plantuml", and 20+ more Kroki types). When rendering into a local
    clone of the experiment repository, save the result as a PDF under
    `.research/results/diagram/`, then commit and push — the LaTeX build
    collects every `*.pdf` under `.research/results/`. `output_path` must
    end with .pdf, .svg, or .png; PDF conversion happens locally from the
    SVG (vector). Types whose SVG embeds
    HTML labels (e.g. mermaid) fall back to a raster PDF automatically —
    prefer "graphviz" / "plantuml" when you want vector text. Rendering uses
    the public https://kroki.io by default — set KROKI_BASE_URL to a
    self-hosted instance to keep unpublished diagrams private. No API keys
    required.
    """
    return await render_diagram_usecase(
        _kroki_client(), diagram_type, diagram_source, output_path
    )
