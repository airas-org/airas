from __future__ import annotations

from typing import Any, Literal, Optional

from pydantic import BaseModel, Field

from airas.core.types.paper_values import (
    ClaimStatus,
    ComputedValue,
    TableSpec,
    ValueDeclaration,
)

RECORD_SCHEMA_VERSION = 1
CLAIM_ID_PATTERN = r"^c[1-9][0-9]*$"


class RunDeclaration(BaseModel):
    run_id: str = Field(description="Results directory this run will produce")
    description: str = ""
    supersedes: Optional[str] = None


class ClaimDeclaration(BaseModel):
    id: str = Field(pattern=CLAIM_ID_PATTERN)
    statement: str = Field(description="One assertive sentence")
    criterion: str = Field(
        description="Prose falsification line: below this the claim is refuted"
    )
    predicted_interval: str = Field(
        description="Predicted range (never a point) and where it comes from"
    )
    run_ids: list[str] = Field(
        min_length=1, description="Declared runs that must execute to test this"
    )
    value_keys: list[str] = Field(
        default_factory=list,
        description="Declared value keys the claim is judged on",
    )
    supersedes: Optional[str] = None


class ChartDeclaration(BaseModel):
    path: str = Field(
        description="Chart file path relative to .research/results/chart/"
    )
    format: Literal["svg", "png"]
    spec: dict[str, Any] = Field(
        description="Unresolved Vega-Lite spec; data points are 'metric:' refs"
    )
    supersedes: Optional[str] = None


class PreregSection(BaseModel):
    hypothesis: str
    design: str
    runs: list[RunDeclaration] = Field(min_length=1)
    claims: list[ClaimDeclaration] = Field(default_factory=list)
    values: list[ValueDeclaration] = Field(default_factory=list)
    tables: list[TableSpec] = Field(default_factory=list)
    charts: list[ChartDeclaration] = Field(default_factory=list)
    notes: list[str] = Field(default_factory=list)


class LinkBase(BaseModel):
    repo_url: str = Field(description="Normalized https URL of the origin remote")
    ref: str = Field(description="Branch the paper links into")


class RenderedChart(BaseModel):
    path: str
    renderer: str = Field(description="e.g. 'vl-convert-python 1.7.0'")


class RunResult(BaseModel):
    run_id: str
    execution_id: Optional[str] = Field(
        default=None, description="Platform run this data came from"
    )
    run_commit: Optional[str] = Field(
        default=None, description="Commit that run executed"
    )
    metrics: Any = Field(description="Verbatim content of the run's metrics file")


class RecordResults(BaseModel):
    runs: list[RunResult] = Field(default_factory=list)
    values: list[ComputedValue] = Field(default_factory=list)
    claim_status: list[ClaimStatus] = Field(default_factory=list)
    charts: list[RenderedChart] = Field(default_factory=list)
    link_base: Optional[LinkBase] = None


class PaperRecord(BaseModel):
    schema_version: int = RECORD_SCHEMA_VERSION
    prereg: PreregSection
    results: RecordResults = Field(default_factory=RecordResults)
