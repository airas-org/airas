from __future__ import annotations

from typing import Any, Literal, Optional

from pydantic import BaseModel, Field

from airas.core.types.paper_values import TableSpec

RECORD_SCHEMA_VERSION = 2
CLAIM_ID_PATTERN = r"^c[1-9][0-9]*$"
DESIGN_ID_PATTERN = r"^d[1-9][0-9]*$"

TARGET_OP = Literal["value", "mean", "std", "diff", "pct_improve"]


class ResearchRecord(BaseModel):
    schema_version: int = RECORD_SCHEMA_VERSION
    hypothesis: Hypothesis
    tables: list[TableSpec] = Field(default_factory=list)
    charts: list[ChartDeclaration] = Field(default_factory=list)
    notes: list[str] = Field(default_factory=list)
    link_base: Optional[LinkBase] = None


class Hypothesis(BaseModel):
    statement: str
    claims: list[ClaimDeclaration] = Field(default_factory=list)
    designs: list[DesignDeclaration] = Field(default_factory=list)


class ClaimDeclaration(BaseModel):
    id: str = Field(pattern=CLAIM_ID_PATTERN)
    statement: str = Field(description="One assertive sentence")
    target: Target
    criterion: Bound = Field(description="Outside this range the claim is refuted")
    predicted_interval: Bound = Field(description="What is expected — never a point")
    rationale: str = Field(default="", description="Where the prediction comes from")
    withdrawn: bool = False
    evaluations: list[ClaimEvaluation] = Field(default_factory=list)


class Bound(BaseModel):
    min: Optional[float] = None
    max: Optional[float] = None

    def contains(self, value: float) -> bool:
        if self.min is not None and value < self.min:
            return False
        if self.max is not None and value > self.max:
            return False
        return True

    def describe(self) -> str:
        if self.min is not None and self.max is not None:
            return f"{self.min} .. {self.max}"
        if self.max is not None:
            return f"<= {self.max}"
        if self.min is not None:
            return f">= {self.min}"
        return "unbounded"


class Target(BaseModel):
    op: TARGET_OP = "value"
    refs: list[str] = Field(
        min_length=1,
        description=(
            "Metric references '<run_id>.path.to.metric'; 'comparison.…' "
            "addresses the aggregated metrics directory"
        ),
    )
    abs: bool = Field(
        default=False, description="Take the absolute value of the result"
    )
    round: Optional[int] = Field(default=None, ge=0, le=10)


class ClaimEvaluation(BaseModel):
    at_commit: Optional[str] = Field(
        default=None, description="Commit this realization was written in"
    )
    used_executions: dict[str, str] = Field(
        default_factory=dict,
        description="run_id -> execution_id that supplied the number",
    )
    value: float
    display: str
    verified: bool = Field(
        description=(
            "Every run the target references has results whose commit is an "
            "ancestor of HEAD and already contained this identical claim"
        )
    )
    criterion_met: bool = Field(
        description="The value fell inside the frozen criterion — a separate "
        "question from `verified`, which only says the claim was properly tested"
    )
    detail: str = ""


class DesignDeclaration(BaseModel):
    id: str = Field(pattern=DESIGN_ID_PATTERN)
    summary: str = ""
    withdrawn: bool = False
    runs: list[RunDeclaration] = Field(default_factory=list)


class RunDeclaration(BaseModel):
    """A planned run. Parameters live in the repository's own config files,
    which the commit already fixes, so only what the commit *cannot* fix is
    declared here: the overrides the dispatch will apply. Declaring them is
    what makes "we said full and ran pilot" detectable."""

    run_id: str = Field(description="Results directory this run produces; repo-unique")
    description: str = ""
    overrides: dict[str, Any] = Field(
        default_factory=dict,
        description="Parameters this run will be dispatched with, e.g. {'mode': 'full'}",
    )
    withdrawn: bool = False
    executions: list[Execution] = Field(default_factory=list)


class Execution(BaseModel):
    """One actual run on the compute platform. Facts; never rewritten.

    Running the same configuration again appends another execution rather
    than replacing this one, so "we ran it three times" stays in the record.

    The commit alone does not determine what ran: the executor can override
    parameters at dispatch (`mode=full` turns 200 architectures into 1000
    without touching a tracked file), so the resolved configuration is
    recorded here rather than inferred from the tree.
    """

    execution_id: Optional[str] = Field(
        default=None, description="Platform run id this data came from"
    )
    commit: Optional[str] = Field(default=None, description="Commit that run executed")
    overrides: dict[str, Any] = Field(
        default_factory=dict,
        description="Parameters the dispatch overrode on top of the commit",
    )
    config: dict[str, Any] = Field(
        default_factory=dict,
        description="Resolved configuration the run actually used",
    )
    inputs: Optional[InputRef] = None
    evaluation: Optional[EvalReport] = None
    metrics: Any = Field(
        default=None, description="Verbatim content of the run's metrics file"
    )


class InputRef(BaseModel):
    path: str = Field(description="Repository-relative path of the inputs file")
    sha256: str


class EvalReport(BaseModel):
    task_type: str
    task_signature: Optional[str] = None
    inputs_sha256: Optional[str] = None
    versions: dict[str, str] = Field(default_factory=dict)
    metrics: dict[str, float] = Field(default_factory=dict)
    curves: dict[str, Any] = Field(
        default_factory=dict, description="Series the paper may plot"
    )
    inputs_summary: dict[str, float] = Field(default_factory=dict)
    skipped: dict[str, Any] = Field(
        default_factory=dict,
        description="Metrics that could not be computed, with reasons — a "
        "result in its own right, so it is carried rather than dropped",
    )


class RenderedChart(BaseModel):
    at_commit: Optional[str] = None
    renderer: str = Field(description="e.g. 'vl-convert-python 1.7.0'")


class ChartDeclaration(BaseModel):
    path: str = Field(description="Chart path relative to .research/results/chart/")
    format: Literal["svg", "png"]
    spec: dict[str, Any] = Field(
        description="Unresolved Vega-Lite spec; data points are 'metric:' refs"
    )
    withdrawn: bool = False
    renders: list[RenderedChart] = Field(default_factory=list)


class LinkBase(BaseModel):
    """Where a value macro links to.

    Only the remote is stored. The ref is resolved at render and verification
    time as the commit that last wrote record.json, which pins the link to the
    record as it stood when the number was produced — storing it here instead
    would be circular, since the sha is not known until the write is
    committed.
    """

    repo_url: str = Field(description="Normalized https URL of the origin remote")
