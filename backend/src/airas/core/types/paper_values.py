from __future__ import annotations

from typing import Literal, Optional

from pydantic import BaseModel, Field

VALUE_OP = Literal["value", "mean", "std", "diff", "pct_improve"]

# Keys become LaTeX \csname parts and JSON keys; keep them boring.
KEY_PATTERN = r"^[a-z][a-z0-9_]*$"


class ValueDeclaration(BaseModel):
    """A paper value declared as an expression over measured metrics.

    The declaration names *which* metrics are used and *how* they combine;
    the numbers themselves are always read from the run outputs and
    computed by deterministic code, never taken from the caller.
    """

    key: str = Field(
        pattern=KEY_PATTERN,
        description="Name the paper uses as \\airasval{key}",
    )
    op: VALUE_OP = Field(
        default="value",
        description=(
            "value: the single ref as-is; mean/std: over all refs; "
            "diff: refs[0] - refs[1]; "
            "pct_improve: (refs[0] - refs[1]) / |refs[1]| * 100"
        ),
    )
    refs: list[str] = Field(
        min_length=1,
        description=(
            "Metric references 'run_id.path.to.metric' into that run's "
            "metrics.json ('comparison.…' addresses aggregated metrics)"
        ),
    )
    round: Optional[int] = Field(
        default=None,
        ge=0,
        le=10,
        description="Decimal places for display; omitted = shortest form",
    )


class ComputedValue(ValueDeclaration):
    value: float = Field(description="The computed value, unrounded")
    display: str = Field(description="Exactly what \\airasval{key} prints")


class PaperValues(BaseModel):
    """The machine-computed numbers a paper is allowed to state."""

    values: list[ComputedValue] = Field(default_factory=list)


class ProvenanceDirCheck(BaseModel):
    """One results directory checked against an execution platform's storage."""

    dir: str = Field(description="Directory name under .research/results/")
    run_id: Optional[str] = Field(
        default=None,
        description=(
            "Platform run the provenance manifest declares for this directory"
        ),
    )
    commit_hash: Optional[str] = Field(
        default=None, description="Commit that run executed"
    )
    commit_in_history: Optional[bool] = Field(
        default=None,
        description=("Whether that commit is an ancestor of the local clone's HEAD"),
    )
    matched: bool = Field(
        description=(
            "The declared, completed run holds byte-identical metrics for "
            "this directory and its commit is an ancestor of HEAD"
        )
    )
    sibling_run_ids: list[str] = Field(
        default_factory=list,
        description=(
            "Other completed runs of the same commit — the same code was "
            "executed more than once, so which run backs the paper was a "
            "choice; listed to make that choice reviewable"
        ),
    )
    detail: str = ""


class ProvenanceCheckResult(BaseModel):
    source: str = Field(description="The platform consulted, e.g. 'seyval'")
    status: Literal["verified", "mismatch", "unavailable"] = Field(
        description=(
            "verified: every referenced directory is backed by a completed "
            "run's stored bytes; mismatch: at least one is not (tampering "
            "or unknown provenance); unavailable: the platform could not "
            "be consulted (no credentials, no registered repository, "
            "network)"
        )
    )
    checks: list[ProvenanceDirCheck] = Field(default_factory=list)
    detail: str = ""


class PaperValuesVerificationReport(BaseModel):
    """What the deterministic value checks found.

    `ok` covers only the machine-checkable part: the stored values match a
    recomputation from the run outputs, values.tex is byte-identical to a
    regeneration, every referenced key is defined, and — when a
    provenance cross-check ran — no mismatch against the execution
    platform's stored run outputs. `unverified` is review input, not a
    failure.
    """

    ok: bool = Field(
        description=(
            "True only if all required files exist, values.json matches a "
            "recomputation from the run outputs, values.tex matches a "
            "regeneration byte-for-byte, and the provenance cross-check "
            "(if performed) found no mismatch"
        )
    )
    values_match: bool = Field(
        description="Stored values equal a recomputation from the run outputs"
    )
    values_tex_match: bool = Field(
        description="values.tex is byte-identical to a regeneration"
    )
    mismatches: list[str] = Field(default_factory=list)
    missing_files: list[str] = Field(default_factory=list)
    undefined_keys: list[str] = Field(
        default_factory=list,
        description=(
            "\\airasval keys main.tex references that values.json does not "
            "define — these would render as ??airasval:key?? in the PDF"
        ),
    )
    unverified: list[str] = Field(
        default_factory=list,
        description="Contents of every \\unverified{...} in main.tex",
    )
    provenance: Optional[ProvenanceCheckResult] = Field(
        default=None,
        description=(
            "Cross-check of the local metrics files against the execution "
            "platform's stored run outputs; None when the check was not "
            "requested"
        ),
    )
