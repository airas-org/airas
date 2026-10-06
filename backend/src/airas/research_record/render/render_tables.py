from __future__ import annotations

import json
from typing import Any

from airas.core.types.map_record_to_publication import TableSpec
from airas.research_record.render._latex_text import AUTO_GENERATED_HEADER
from airas.research_record.render._resolve_ref import resolve_ref
from airas.research_record.render.render_paper_values import passage_line, record_line

TABLES_DIR_NAME = "tables"


def render_table_tex(
    spec: TableSpec, metrics_data: dict[str, Any], record_json: str | None = None
) -> str:
    # Core LaTeX only (no booktabs), so the output compiles under every
    # bundled template. The cell at (row, column) is always
    # <row.run_id>.<column.ref_path>: a label cannot be paired with
    # another run's number. With `record_json` (the record as the linked
    # commit holds it, see values.tex) each cell links to its line there, like
    # \airasval does: a measured or difference cell to the metric's line, a
    # published cell to its passage's quote.
    data = json.loads(record_json) if record_json else None
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
            line = None
            if column.ref_path is not None:
                ref = f"{row.run_id}.{column.ref_path}"
                value = resolve_ref(metrics_data, ref)
                line = record_line(data, row.run_id, column.ref_path) if data else None
            if column.reference is not None:
                if row.run_id not in column.reference.values:
                    raise ValueError(
                        f"column {column.header!r} has no published value for "
                        f"run '{row.run_id}'"
                    )
                published = column.reference.values[row.run_id]
                value = value - published if column.ref_path is not None else published
                if column.ref_path is None and data:
                    line = passage_line(data, column.reference.quoted_passage_ids[0])
            text = (
                f"{value:.{column.round}f}"
                if column.round is not None
                else f"{value:g}"
            )
            cells.append(rf"\airasrecordlink[\#L{line}]{{{text}}}" if line else text)
        lines.append(" & ".join(cells) + r" \\")
    lines += [r"\hline", r"\end{tabular}", r"\end{table}"]
    return "\n".join(lines) + "\n"
