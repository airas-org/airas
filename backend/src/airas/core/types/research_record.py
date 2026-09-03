"""The canonical research record: `.research/record.json`.

A tree, read top-down as "to support this hypothesis, these claims; to
verify this claim, these designs; a design is these runs; a run has been
executed these times":

    hypotheses[] → claims[] → designs[] → runs[] → results[]

Two kinds of content live in it. The *declarations* — every field except
`results[]` and `verified` — are written by the agent before any experiment
runs and frozen by the first commit. The *facts* — `results[]` and
`verified` — are appended by `update_record` from the run outputs and the
platform's records, and never by hand.

The whole file is append-only in the containment sense: a later revision
must contain the earlier one whole. Objects may gain keys, lists may grow at
the end, and nothing already written changes. That is what lets the record
be trusted from its git history alone: a rewritten criterion, a dropped
execution or a reordered list all fail the same single rule.
"""

from __future__ import annotations

from typing import Any, Literal, Optional

from pydantic import BaseModel, Field

from airas.core.types.paper_values import TableSpec

HYPOTHESIS_ID_PATTERN = r"^h[1-9][0-9]*$"
CLAIM_ID_PATTERN = r"^c[1-9][0-9]*$"
DESIGN_ID_PATTERN = r"^d[1-9][0-9]*$"


class ResearchRecord(BaseModel):
    hypotheses: list[Hypothesis] = Field(default_factory=list)


class Hypothesis(BaseModel):
    id: str = Field(pattern=HYPOTHESIS_ID_PATTERN)
    statement: str = Field(description="The hypothesis itself, in prose")
    claims: list[ClaimDeclaration] = Field(default_factory=list)
    tables: list[TableSpec] = Field(default_factory=list)
    charts: list[ChartDeclaration] = Field(default_factory=list)
    notes: list[str] = Field(default_factory=list)


class ClaimDeclaration(BaseModel):
    """One assertion the hypothesis rests on, and the experiments that test it.

    What the claim's condition is, whether it was met, and whether the claim
    was declared before its runs executed are not modelled yet (TODO).
    `verified` says only that every run under the claim has results — the
    data the claim rests on is in.
    """

    id: str = Field(pattern=CLAIM_ID_PATTERN)
    statement: str = Field(description="One assertive sentence")
    designs: list[DesignDeclaration] = Field(
        default_factory=list,
        description="The experimental designs needed to verify this claim",
    )
    withdrawn: bool = Field(
        default=False,
        description="Retired without deletion; a later entry with the same id "
        "is the revision",
    )
    # Set to true by update_record once the procedure is complete, and never
    # back. This is the one value in the record that changes after being
    # written, so containment permits exactly that transition (false -> true)
    # and nothing else. A later recomputation that disagrees with a stored
    # true — after a history rewrite, say — is a verification failure, not a
    # value to overwrite.
    verified: bool = Field(
        default=False,
        description="Every run under this claim has results",
    )


class DesignDeclaration(BaseModel):
    id: str = Field(pattern=DESIGN_ID_PATTERN)
    summary: str = ""
    runs: list[RunDeclaration] = Field(default_factory=list)
    withdrawn: bool = False


class RunDeclaration(BaseModel):
    """One unit of execution: a results directory and the conditions it runs under."""

    run_id: str = Field(description="Results directory this run produces; repo-unique")
    description: str = ""
    params: dict[str, Any] = Field(
        default_factory=dict,
        description="Conditions this run is declared to be dispatched with, "
        "e.g. {'mode': 'full'}. Checked against what the platform recorded",
    )
    withdrawn: bool = False
    results: list[RunResult] = Field(default_factory=list)


class RunResult(BaseModel):
    """What one execution of the run produced. Facts; never rewritten.

    Running again appends another entry, so "we ran it three times" stays in
    the record. Everything here comes from the platform's own record or from
    files the platform stored — nothing from the experiment code's word —
    and the verifier holds each field to its source.
    """

    id: str = Field(description="The platform's id for this execution")
    commit: Optional[str] = Field(default=None, description="Commit that run executed")
    eval_inputs: Optional[InputRef] = Field(
        default=None,
        description="The file the experiment wrote for the evaluation layer "
        "(raw predictions and references): the re-derivation anchor",
    )
    eval_report: Optional[EvalReport] = Field(
        default=None, description="The evaluation layer's report on those inputs"
    )
    metrics: Any = Field(
        default=None,
        description="The run's metrics file, verbatim: every number the paper "
        "may cite, from the evaluation layer or from the experiment itself",
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
        "result too, not an omission",
    )


class RenderedChart(BaseModel):
    renderer: str = Field(description="e.g. 'vl-convert-python 1.7.0'")


class ChartDeclaration(BaseModel):
    path: str = Field(description="Chart path relative to .research/results/chart/")
    format: Literal["svg", "png"]
    spec: dict[str, Any] = Field(
        description="Unresolved Vega-Lite spec; data points are 'metric:' refs"
    )
    withdrawn: bool = False
    renders: list[RenderedChart] = Field(default_factory=list)
