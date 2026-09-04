from __future__ import annotations

import re
from typing import Any

import vl_convert as vlc
from pydantic import BaseModel

from airas.core.research_paths import RECORD_PATH
from airas.core.types.map_record_to_publication import PaperValue, TableSpec
from airas.core.types.research_record import ResearchRecord, active


# ------------------------------------------ \\airasval{...} -> a number
def match_run_id(metrics_data: dict[str, Any], ref: str) -> str | None:
    return max(
        (k for k in metrics_data if ref == k or ref.startswith(k + ".")),
        key=len,
        default=None,
    )


def used_result_dirs(record: ResearchRecord, metrics_data: dict[str, Any]) -> set[str]:
    """Every results directory a declared run or table row reads."""
    dirs = {run_id for run_id in record.run_index() if run_id in metrics_data}
    for hypothesis in record.active_hypotheses():
        for spec in active(hypothesis.tables, "key"):
            for row in spec.rows:
                if row.run_id in metrics_data:
                    dirs.add(row.run_id)
    return dirs


def _walk(node: Any, remainder: str, ref: str, where: str) -> float:
    for segment in remainder.split(".") if remainder else []:
        try:
            node = node[int(segment)] if isinstance(node, list) else node[segment]
        except (KeyError, IndexError, ValueError, TypeError):
            raise ValueError(f"'{ref}': nothing at '{segment}' in {where}") from None
    if isinstance(node, bool) or not isinstance(node, (int, float)):
        raise ValueError(f"'{ref}' is not a number: {node!r}")
    return float(node)


def resolve_ref(metrics_data: dict[str, Any], ref: str) -> float:
    """Resolve '<run_id>.<metric path>' against the committed results files."""
    run_id = match_run_id(metrics_data, ref)
    if run_id is None:
        available = ", ".join(sorted(metrics_data))
        raise ValueError(f"'{ref}' matches no run id (available: {available})")
    return _walk(metrics_data[run_id], ref[len(run_id) + 1 :], ref, f"run '{run_id}'")


def format_display(value: float, round_digits: int | None) -> str:
    if round_digits is not None:
        return f"{value:.{round_digits}f}"
    return f"{value:g}"


def _walk_any(node: Any, path: str) -> Any:
    for segment in path.split(".") if path else []:
        node = node[int(segment)] if isinstance(node, list) else node[segment]
    return node


def resolve_paper_ref(
    record: ResearchRecord,
    metrics_data: dict[str, Any],
    ref: str,
) -> str:
    """Resolve what \\airasval{...} addresses, returning what it prints.

    Two forms, both writable before any run exists — which is what lets the
    preregistered paper be written in full:

      <run_id>.params.<path>    a condition the run was declared with
      <run_id>.<metric path>    a metric of a declared run, read directly

    The params form reads the declaration; the gate checks that declaration
    against what the platform recorded for the dispatch, so citing a batch
    size cites a condition the run was held to, not what the code said it
    was doing. Derived numbers (a claim's target) are not modelled yet.
    """
    head, _, tail = ref.partition(".")

    runs = record.run_index()
    if head in runs and tail.startswith("params."):
        try:
            params = runs[head].params
            if isinstance(params, BaseModel):
                params = params.model_dump()
            node = _walk_any(params, tail[len("params.") :])
        except (KeyError, IndexError, ValueError, TypeError):
            raise ValueError(
                f"'{ref}': run '{head}' declares no such parameter"
            ) from None
        if isinstance(node, bool) or isinstance(node, (dict, list)):
            raise ValueError(f"'{ref}' is not a scalar: {node!r}")
        # Parameters are legitimately strings ("cifar10", "jacob_cov"), so
        # only numbers get rounded; anything else prints as written.
        return (
            format_display(float(node), None)
            if isinstance(node, (int, float))
            else str(node)
        )

    return format_display(resolve_ref(metrics_data, ref), None)


def resolve_paper_values(
    record: ResearchRecord, metrics_data: dict[str, Any], used_keys: list[str]
) -> tuple[list[PaperValue], list[str]]:
    """Every \\airasval the paper uses, in the order it uses them.

    Shared by the tool that writes values.tex and the check that regenerates
    it: two builders would have to agree byte-for-byte forever, and the first
    time they disagreed the regeneration check would fail on a paper nobody
    had touched.
    """
    values: list[PaperValue] = []
    undefined: list[str] = []
    for ref in dict.fromkeys(used_keys):
        try:
            display = resolve_paper_ref(record, metrics_data, ref)
        except ValueError:
            undefined.append(ref)
            continue
        values.append(PaperValue(ref=ref, display=display, derivation=ref))
    return values, undefined


# ------------------------------------------------------------ values.tex
VALUES_TEX_FILENAME = "values.tex"

_VALUES_TEX_HEADER = (
    "% AUTO-GENERATED by the update_record tool. DO NOT EDIT.\n"
    "% verify_paper_values regenerates this file from record.json and the\n"
    "% run outputs and fails on any difference, so manual edits always surface."
)

# Characters safe both in a URL and inside \href's first argument (a %
# would comment out the rest of the line, a # would break macro parsing).
_URL_SAFE = re.compile(r"^[A-Za-z0-9:/._~-]+$")


def record_blob_url(repo_url: str | None, ref: str | None) -> str | None:
    """Link into the record at a pinned commit.

    A branch link would resolve to whatever the record says later — it keeps
    growing — so the link names the commit that last wrote it, which is the
    state that produced the number being clicked. Both parts are derived at
    render time (the origin remote, the commit that wrote the record) rather
    than stored in the record, which has no reason to know where it lives.
    """
    if not ref or not repo_url:
        return None
    url = f"{repo_url}/blob/{ref}/{RECORD_PATH}"
    return url if _URL_SAFE.match(url) else None


def render_values_tex(
    values: list[PaperValue], repo_url: str | None, ref: str | None = None
) -> str:
    url = record_blob_url(repo_url, ref)
    lines = [
        _VALUES_TEX_HEADER,
        r"\makeatletter",
        r"\newcommand{\airasval}[1]{\@ifundefined{airasval@#1}"
        r"{\airasvalmissing{#1}}{\csname airasval@#1\endcsname}}",
        r"\newcommand{\airasvalmissing}[1]{\textbf{??airasval:\detokenize{#1}??}}",
        r"\providecommand{\unverified}[1]{#1}",
        # \ifdefined at use time: hyperref may load after this file (mdpi
        # loads it at begindocument), and without it the value stays plain.
        (
            rf"\newcommand{{\airasrecordlink}}[1]{{\ifdefined\href"
            rf"\href{{{url}}}{{#1}}\else#1\fi}}"
            if url
            else r"\newcommand{\airasrecordlink}[1]{#1}"
        ),
    ]
    for value in values:
        if value.derivation:
            lines.append(f"% {value.ref} = {value.derivation}")
        lines.append(
            rf"\expandafter\def\csname airasval@{value.ref}\endcsname"
            rf"{{\airasrecordlink{{{value.display}}}}}"
        )
    lines.append(r"\makeatother")
    return "\n".join(lines) + "\n"


# --------------------------------------------------------- tables/<key>.tex
TABLES_DIR_NAME = "tables"

_TABLES_TEX_HEADER = (
    "% AUTO-GENERATED by the update_record tool. DO NOT EDIT.\n"
    "% verify_paper_values regenerates this file from record.json and the\n"
    "% run outputs and fails on any difference, so manual edits always surface."
)


def table_tex_relpath(key: str) -> str:
    return f"{TABLES_DIR_NAME}/{key}.tex"


def render_table_tex(spec: TableSpec, metrics_data: dict[str, Any]) -> str:
    # Core LaTeX only (no booktabs), so the output compiles under every
    # bundled template. The cell at (row, column) is always
    # <row.run_id>.<column.ref_path>: a label cannot be paired with
    # another run's number.
    column_layout = "l" + "r" * len(spec.columns)
    header_cells = [""] + [column.header for column in spec.columns]

    lines = [
        _TABLES_TEX_HEADER,
        r"\begin{table}[t]",
        r"\centering",
        rf"\caption{{{spec.caption}}}",
        rf"\label{{{spec.label or f'tab:{spec.key}'}}}",
        rf"\begin{{tabular}}{{{column_layout}}}",
        r"\hline",
        " & ".join(header_cells) + r" \\",
        r"\hline",
    ]
    for row in spec.rows:
        cells = [row.label]
        for column in spec.columns:
            value = resolve_ref(metrics_data, f"{row.run_id}.{column.ref_path}")
            cells.append(format_display(value, column.round))
        lines.append(" & ".join(cells) + r" \\")
    lines += [r"\hline", r"\end{tabular}", r"\end{table}"]
    return "\n".join(lines) + "\n"


def table_result_dirs(specs: list[TableSpec], metrics_data: dict[str, Any]) -> set[str]:
    return {
        d
        for spec in specs
        for row in spec.rows
        if (d := match_run_id(metrics_data, row.run_id)) is not None
    }


# ---------------------------------------------------------------- charts
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
    from airas.usecases.publication.map_record_to_publication import resolve_ref

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


def chart_result_dirs(record: ResearchRecord, metrics_data: dict[str, Any]) -> set[str]:
    from airas.usecases.publication.map_record_to_publication import match_run_id

    dirs: set[str] = set()
    for declaration in record.active_charts():
        try:
            _, refs = substitute_chart_refs(declaration.spec, metrics_data)
        except Exception:
            continue  # verify_charts reports the breakage itself
        for ref in refs:
            run_id = match_run_id(metrics_data, ref)
            if run_id is not None:
                dirs.add(run_id)
    return dirs
