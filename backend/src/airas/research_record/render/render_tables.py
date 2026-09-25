from __future__ import annotations

from typing import Any

from airas.core.types.map_record_to_publication import TableSpec
from airas.research_record.render._latex_text import AUTO_GENERATED_HEADER
from airas.research_record.render._resolve_ref import resolve_ref

TABLES_DIR_NAME = "tables"


def render_table_tex(spec: TableSpec, metrics_data: dict[str, Any]) -> str:
    # Core LaTeX only (no booktabs), so the output compiles under every
    # bundled template. The cell at (row, column) is always
    # <row.run_id>.<column.ref_path>: a label cannot be paired with
    # another run's number.
    column_layout = "l" + "r" * len(spec.columns)
    header_cells = [""] + [column.header for column in spec.columns]

    lines = [
        AUTO_GENERATED_HEADER,
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
            value = 0.0
            if column.ref_path is not None:
                value = resolve_ref(metrics_data, f"{row.run_id}.{column.ref_path}")
            if column.reference is not None:
                if row.run_id not in column.reference.values:
                    raise ValueError(
                        f"column {column.header!r} has no published value for "
                        f"run '{row.run_id}'"
                    )
                published = column.reference.values[row.run_id]
                value = value - published if column.ref_path is not None else published
            cells.append(
                f"{value:.{column.round}f}"
                if column.round is not None
                else f"{value:g}"
            )
        lines.append(" & ".join(cells) + r" \\")
    lines += [r"\hline", r"\end{tabular}", r"\end{table}"]
    return "\n".join(lines) + "\n"
