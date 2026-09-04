from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field

# Keys become LaTeX \csname parts and JSON keys; keep them boring.
KEY_PATTERN = r"^[a-z][a-z0-9_]*$"


class PaperValue(BaseModel):
    ref: str = Field(description="What \\airasval{...} contains")
    display: str = Field(description="Exactly what it prints")
    derivation: str = Field(
        default="", description="Human-readable note of where the number came from"
    )


class TableColumnSpec(BaseModel):
    header: str = Field(description="Column heading (LaTeX allowed)")
    ref_path: str = Field(
        description=(
            "Metric path inside each row's metrics.json, e.g. 'accuracy' "
            "or 'loss.final' — resolved per row as '<run_id>.<ref_path>'"
        )
    )
    round: Optional[int] = Field(
        default=None,
        ge=0,
        le=10,
        description="Decimal places for display; omitted = shortest form",
    )


class TableRowSpec(BaseModel):
    run_id: str = Field(description="Results directory the row's numbers come from")
    label: str = Field(description="Row heading, e.g. 'Ours' (LaTeX allowed)")


class TableSpec(BaseModel):
    key: str = Field(
        pattern=KEY_PATTERN,
        description="Table name; rendered to tables/<key>.tex",
    )
    caption: str = Field(description="Table caption (LaTeX allowed)")
    label: Optional[str] = Field(
        default=None, description="\\label value; defaults to tab:<key>"
    )
    columns: list[TableColumnSpec] = Field(min_length=1)
    rows: list[TableRowSpec] = Field(min_length=1)
