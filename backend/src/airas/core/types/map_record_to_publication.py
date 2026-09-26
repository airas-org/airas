from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field, model_validator

# Keys become LaTeX \csname parts and JSON keys; keep them boring.
KEY_PATTERN = r"^[a-z][a-z0-9_]*$"


class PaperValue(BaseModel):
    ref: str = Field(description="What \\airasval{...} contains")
    display: str = Field(description="Exactly what it prints")
    derivation: str = Field(
        default="", description="Human-readable note of where the number came from"
    )
    line: Optional[int] = Field(
        default=None, description="Line of record.json that holds the number"
    )


class ReferenceValues(BaseModel):
    passage: str = Field(
        description="Passage id the values are read from, e.g. 's1.p5'"
    )
    values: dict[str, float] = Field(
        description="run_id -> the published value that row is compared with"
    )


class TableColumnSpec(BaseModel):
    header: str = Field(description="Column heading (LaTeX allowed)")
    ref_path: Optional[str] = Field(
        default=None,
        description=(
            "Metric path inside each row's metrics.json, e.g. 'accuracy' "
            "or 'loss.final' — resolved per row as '<run_id>.<ref_path>'"
        ),
    )
    reference: Optional[ReferenceValues] = Field(
        default=None,
        description="Published values per row; alone the column shows them, "
        "with ref_path it shows measured minus published",
    )
    round: Optional[int] = Field(
        default=None,
        ge=0,
        le=10,
        description="Decimal places for display; omitted = shortest form",
    )

    @model_validator(mode="after")
    def _some_source(self) -> "TableColumnSpec":
        if self.ref_path is None and self.reference is None:
            raise ValueError(f"column {self.header!r} needs ref_path or reference")
        return self


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
