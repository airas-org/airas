"""Deterministic tables and metric-referenced charts.

Both close the same gap: a label being paired with a number its run did
not produce. Tables bind (row, column) to run_id.ref_path; charts forbid
literal data numbers and re-render from the declared spec.
"""

from pathlib import Path

import pytest

from airas.core.types.paper_values import (
    PaperTables,
    TableColumnSpec,
    TableRowSpec,
    TableSpec,
)
from airas.usecases.publication.paper_values.charts import (
    CHART_DIR,
    chart_result_dirs,
    render_chart_bytes,
    substitute_chart_refs,
    verify_charts,
    write_chart_sidecar,
)
from airas.usecases.publication.paper_values.tables import (
    compute_paper_tables,
    render_table_tex,
    table_result_dirs,
)
from airas.usecases.publication.paper_values.verify import _verify_tables

METRICS_DATA = {
    "run_1": {"accuracy": 0.871, "loss": {"final": 0.32}},
    "run_2": {"accuracy": 0.902, "loss": {"final": 0.28}},
}

TABLE = TableSpec(
    key="main_results",
    caption="Results.",
    columns=[
        TableColumnSpec(header="Accuracy", ref_path="accuracy", round=3),
        TableColumnSpec(header="Loss", ref_path="loss.final", round=2),
    ],
    rows=[
        TableRowSpec(run_id="run_2", label="Ours"),
        TableRowSpec(run_id="run_1", label="Baseline"),
    ],
)


# --------------------------------------------------
# Tables
# --------------------------------------------------


def test_table_cells_come_from_the_row_run() -> None:
    tex = render_table_tex(TABLE, METRICS_DATA)
    assert r"Ours & 0.902 & 0.28 \\" in tex
    assert r"Baseline & 0.871 & 0.32 \\" in tex
    assert r"\label{tab:main_results}" in tex


def test_table_fails_on_unknown_metric() -> None:
    spec = TABLE.model_copy(
        update={"columns": [TableColumnSpec(header="F1", ref_path="f1")]}
    )
    with pytest.raises(ValueError, match="run_2.f1"):
        render_table_tex(spec, METRICS_DATA)


def test_duplicate_table_keys_rejected() -> None:
    with pytest.raises(ValueError, match="duplicate"):
        compute_paper_tables([TABLE, TABLE], METRICS_DATA)


def test_table_result_dirs_lists_row_runs() -> None:
    assert table_result_dirs(PaperTables(tables=[TABLE])) == {"run_1", "run_2"}


def _write_tables(latex_dir: Path) -> None:
    paper_tables, rendered = compute_paper_tables([TABLE], METRICS_DATA)
    latex_dir.mkdir(parents=True, exist_ok=True)
    (latex_dir / "tables.json").write_text(
        paper_tables.model_dump_json(indent=2) + "\n"
    )
    tables_dir = latex_dir / "tables"
    tables_dir.mkdir()
    for key, tex in rendered.items():
        (tables_dir / f"{key}.tex").write_text(tex)


def test_verify_tables_passes_fresh_generation(tmp_path: Path) -> None:
    _write_tables(tmp_path)
    assert _verify_tables(tmp_path, METRICS_DATA) == []


def test_verify_tables_detects_edited_cell(tmp_path: Path) -> None:
    _write_tables(tmp_path)
    table_path = tmp_path / "tables" / "main_results.tex"
    table_path.write_text(table_path.read_text().replace("0.871", "0.971"))
    problems = _verify_tables(tmp_path, METRICS_DATA)
    assert any("regeneration" in p for p in problems)


def test_verify_tables_detects_swapped_rows_via_regeneration(tmp_path: Path) -> None:
    # Swapping the two data rows keeps every number "real" — and still fails.
    _write_tables(tmp_path)
    table_path = tmp_path / "tables" / "main_results.tex"
    ours = r"Ours & 0.902 & 0.28 \\"
    baseline = r"Baseline & 0.871 & 0.32 \\"
    swapped = (
        table_path.read_text()
        .replace(ours, "@@")
        .replace(baseline, ours)
        .replace("@@", baseline)
    )
    table_path.write_text(swapped)
    assert _verify_tables(tmp_path, METRICS_DATA) != []


def test_verify_tables_rejects_undeclared_table_file(tmp_path: Path) -> None:
    _write_tables(tmp_path)
    (tmp_path / "tables" / "handmade.tex").write_text(
        r"\begin{tabular}{lr} Ours & 0.999 \end{tabular}"
    )
    problems = _verify_tables(tmp_path, METRICS_DATA)
    assert any("handmade.tex" in p and "not declared" in p for p in problems)


# --------------------------------------------------
# Charts
# --------------------------------------------------

CHART_SPEC = {
    "data": {
        "values": [
            {"method": "Ours", "acc": "metric:run_2.accuracy"},
            {"method": "Baseline", "acc": "metric:run_1.accuracy"},
        ]
    },
    "mark": "bar",
    "encoding": {
        "x": {"field": "method", "type": "nominal"},
        "y": {"field": "acc", "type": "quantitative"},
    },
}


def test_chart_refs_resolve_to_measured_numbers() -> None:
    resolved, refs = substitute_chart_refs(CHART_SPEC, METRICS_DATA)
    assert resolved["data"]["values"][0]["acc"] == 0.902
    assert refs == {"run_2.accuracy", "run_1.accuracy"}


def test_chart_rejects_literal_data_numbers() -> None:
    spec = {"data": {"values": [{"method": "Ours", "acc": 0.999}]}, "mark": "bar"}
    with pytest.raises(ValueError, match="literal number"):
        substitute_chart_refs(spec, METRICS_DATA)


def test_chart_rejects_literal_numbers_in_named_datasets() -> None:
    spec = {"datasets": {"d": [{"acc": 0.999}]}, "mark": "bar"}
    with pytest.raises(ValueError, match="literal number"):
        substitute_chart_refs(spec, METRICS_DATA)


def test_chart_rejects_expression_transforms() -> None:
    spec = dict(CHART_SPEC, transform=[{"calculate": "datum.acc + 0.05", "as": "a"}])
    with pytest.raises(ValueError, match="calculate"):
        substitute_chart_refs(spec, METRICS_DATA)


def test_chart_sizes_outside_data_are_allowed() -> None:
    spec = dict(CHART_SPEC, width=320, height=200)
    resolved, _ = substitute_chart_refs(spec, METRICS_DATA)
    assert resolved["width"] == 320


def _write_chart(root: Path) -> Path:
    chart_dir = root / CHART_DIR
    chart_dir.mkdir(parents=True)
    resolved, _ = substitute_chart_refs(CHART_SPEC, METRICS_DATA)
    chart_path = chart_dir / "accuracy.svg"
    chart_path.write_bytes(render_chart_bytes(resolved, "svg"))
    write_chart_sidecar(chart_path, CHART_SPEC, "svg")
    return chart_path


def test_verify_charts_passes_fresh_render(tmp_path: Path) -> None:
    _write_chart(tmp_path)
    assert verify_charts(str(tmp_path), METRICS_DATA) == []


def test_verify_charts_detects_replaced_file(tmp_path: Path) -> None:
    chart_path = _write_chart(tmp_path)
    chart_path.write_bytes(b"<svg>not the rendered chart</svg>")
    problems = verify_charts(str(tmp_path), METRICS_DATA)
    assert any("re-render" in p for p in problems)


def test_verify_charts_detects_tampered_sidecar_data(tmp_path: Path) -> None:
    # Point the sidecar at the other run: the re-render no longer matches
    # the committed bytes.
    chart_path = _write_chart(tmp_path)
    sidecar = chart_path.with_name(chart_path.name + ".chartspec.json")
    sidecar.write_text(
        sidecar.read_text().replace("metric:run_2.accuracy", "metric:run_1.accuracy")
    )
    assert verify_charts(str(tmp_path), METRICS_DATA) != []


def test_verify_charts_rejects_unregistered_chart(tmp_path: Path) -> None:
    chart_dir = tmp_path / CHART_DIR
    chart_dir.mkdir(parents=True)
    (chart_dir / "smuggled.pdf").write_bytes(b"%PDF-1.4 fake")
    problems = verify_charts(str(tmp_path), METRICS_DATA)
    assert any("no declared source" in p for p in problems)


def test_chart_result_dirs_come_from_sidecars(tmp_path: Path) -> None:
    _write_chart(tmp_path)
    assert chart_result_dirs(str(tmp_path), METRICS_DATA) == {"run_1", "run_2"}


def test_verify_charts_ignores_repo_without_charts(tmp_path: Path) -> None:
    assert verify_charts(str(tmp_path), METRICS_DATA) == []


def test_verify_tables_rejects_undeclared_table_in_subdirectory(
    tmp_path: Path,
) -> None:
    # \input reaches any depth, so nesting must not evade the check.
    _write_tables(tmp_path)
    nested = tmp_path / "tables" / "extra"
    nested.mkdir()
    (nested / "handmade.tex").write_text(r"Ours & 0.999 \\")
    problems = _verify_tables(tmp_path, METRICS_DATA)
    assert any("extra/handmade.tex" in p and "not declared" in p for p in problems)


def test_render_chart_bytes_rejects_unknown_format() -> None:
    with pytest.raises(ValueError, match="unsupported chart format"):
        render_chart_bytes({}, "gif")


def test_verify_charts_fails_on_tampered_sidecar_format(tmp_path: Path) -> None:
    chart_path = _write_chart(tmp_path)
    sidecar = chart_path.with_name(chart_path.name + ".chartspec.json")
    sidecar.write_text(sidecar.read_text().replace('"svg"', '"gif"'))
    problems = verify_charts(str(tmp_path), METRICS_DATA)
    assert any("could not be re-rendered" in p for p in problems)


def test_verify_charts_rejects_unregistered_chart_in_subdirectory(
    tmp_path: Path,
) -> None:
    # The LaTeX export collects PDFs recursively, so nesting must not
    # evade the sidecar requirement.
    nested = tmp_path / CHART_DIR / "extra"
    nested.mkdir(parents=True)
    (nested / "smuggled.pdf").write_bytes(b"%PDF-1.4 fake")
    problems = verify_charts(str(tmp_path), METRICS_DATA)
    assert any(
        "extra/smuggled.pdf" in p and "no declared source" in p for p in problems
    )


def test_chart_result_dirs_sees_nested_sidecars(tmp_path: Path) -> None:
    nested_root = tmp_path / CHART_DIR / "extra"
    nested_root.mkdir(parents=True)
    resolved, _ = substitute_chart_refs(CHART_SPEC, METRICS_DATA)
    chart_path = nested_root / "accuracy.svg"
    chart_path.write_bytes(render_chart_bytes(resolved, "svg"))
    write_chart_sidecar(chart_path, CHART_SPEC, "svg")
    assert chart_result_dirs(str(tmp_path), METRICS_DATA) == {"run_1", "run_2"}
    assert verify_charts(str(tmp_path), METRICS_DATA) == []
