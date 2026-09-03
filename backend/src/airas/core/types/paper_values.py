from __future__ import annotations

from typing import Literal, Optional

from pydantic import BaseModel, Field

# Keys become LaTeX \csname parts and JSON keys; keep them boring.
KEY_PATTERN = r"^[a-z][a-z0-9_]*$"


class PaperValue(BaseModel):
    """One number the paper prints, addressed exactly as main.tex writes it."""

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
    withdrawn: bool = Field(
        default=False,
        description="Retired; a later entry with the same key supersedes it",
    )


class ClaimRunCheck(BaseModel):
    run_id: str
    results_present: bool = False
    run_commit: Optional[str] = None
    commit_in_history: Optional[bool] = None
    declared_at_run_commit: Optional[bool] = Field(
        default=None,
        description=(
            "The identical claim and run declarations already existed in "
            "record.json at the commit the run executed — the order proof"
        ),
    )
    detail: str = ""


class ClaimStatus(BaseModel):
    id: str
    verified: bool = Field(
        description=(
            "Every run of the claim has results with a provenance commit in "
            "this branch's history, and the declarations predate that commit"
        )
    )
    criterion_met: Optional[bool] = Field(
        default=None,
        description=(
            "Whether the measured value fell inside the frozen criterion. "
            "Deliberately separate from `verified`, which says only that the "
            "claim was properly preregistered and tested — a refuted claim is "
            "verified and criterion_met=False"
        ),
    )
    value: Optional[float] = Field(
        default=None, description="The measured target value, unrounded"
    )
    display: Optional[str] = Field(default=None, description="Rendered form")
    used_executions: dict[str, str] = Field(
        default_factory=dict, description="run_id -> execution_id that supplied it"
    )
    checks: list[ClaimRunCheck] = Field(default_factory=list)


class ProvenanceDirCheck(BaseModel):
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
            "The declared, completed run holds byte-identical copies of every "
            "file in this directory and produced no file the directory lacks, "
            "its dispatch parameters match the manifest where Seyval reported "
            "them (see parameters_match), and its commit is an ancestor of HEAD"
        )
    )
    files_checked: list[str] = Field(
        default_factory=list,
        description=(
            "Repository-relative paths byte-compared against the run's stored "
            "outputs — every file under the directory, not only metrics.json, "
            "so the inputs the metrics derive from are anchored too"
        ),
    )
    parameters_match: Optional[bool] = Field(
        default=None,
        description=(
            "The manifest's cached overrides/parameters equal what Seyval "
            "recorded for the dispatch; None when Seyval reported none"
        ),
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
    ok: bool = Field(
        description=(
            "True only if all required files exist, record.json matches a "
            "recomputation from the run outputs, values.tex matches a "
            "regeneration byte-for-byte, the record's declaration section "
            "was only ever appended to, and the provenance cross-check "
            "(if performed) found no mismatch"
        )
    )
    stage: Literal["prereg", "results"] = Field(
        default="results",
        description=(
            "prereg: no run outputs exist yet, so only the declarations and "
            "the compile are checked; results: full value verification"
        ),
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
            "\\airasval keys main.tex references that record.json does not "
            "declare — these would render as ??airasval:key?? in the PDF"
        ),
    )
    append_only: Literal["ok", "violated", "unavailable"] = Field(
        default="unavailable",
        description=(
            "Whether every committed revision of record.json only appended "
            "to the declaration section; unavailable = no usable git history"
        ),
    )
    append_only_problems: list[str] = Field(default_factory=list)
    record_commits: list[str] = Field(
        default_factory=list,
        description=(
            "Commits that shaped record.json, oldest first — the first is "
            "the freeze commit"
        ),
    )
    claims: list[ClaimStatus] = Field(
        default_factory=list,
        description="Per-claim verification recomputed from git and provenance",
    )
    claim_status_match: bool = Field(
        default=True,
        description="Stored verified flags equal the recomputation",
    )
    undeclared_result_dirs: list[str] = Field(
        default_factory=list,
        description=(
            "Results directories no declared run accounts for — results "
            "must not exist without a prior declaration"
        ),
    )
    refuted_claims: list[str] = Field(
        default_factory=list,
        description=(
            "Claims that were properly tested but whose criterion was not "
            "met — negative results, reported as such rather than hidden"
        ),
    )
    orphan_runs: list[str] = Field(
        default_factory=list,
        description=(
            "Declared runs no active claim references — legitimate for "
            "supporting numbers, surfaced so undeclared exploration cannot "
            "hide among them"
        ),
    )
    unverified_claims: list[str] = Field(
        default_factory=list,
        description=(
            "Active claim ids not (yet) verified — review input, allowed "
            "at publish but surfaced"
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
