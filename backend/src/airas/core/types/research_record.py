from __future__ import annotations

import math
from enum import StrEnum
from pathlib import Path
from typing import (
    Annotated,
    Any,
    Generic,
    Iterator,
    Literal,
    Mapping,
    Optional,
    Sequence,
    TypeVar,
    Union,
)

from pydantic import BaseModel, Discriminator, Field, Tag, model_validator

from airas.core.research_paths import record_path
from airas.core.types.map_record_to_publication import TableSpec

HYPOTHESIS_ID_PATTERN = r"^h[1-9][0-9]*$"
CLAIM_ID_PATTERN = r"^c[1-9][0-9]*$"
DESIGN_ID_PATTERN = r"^d[1-9][0-9]*$"

Verdict = Literal["supported", "refuted", "inconclusive"]
STANDARD_AXIOMS = ("propext", "Classical.choice", "Quot.sound")


# ---------------------------------------------------------------- verifiers


class VerifierKind(StrEnum):
    SEYVAL = "seyval"
    LEAN = "lean"
    LLM_JUDGE = "llm_judge"


class SeyvalVerifier(BaseModel):
    kind: Literal[VerifierKind.SEYVAL]


class LeanVerifier(BaseModel):
    kind: Literal[VerifierKind.LEAN]
    toolchain: str = Field(default="", description="e.g. leanprover/lean4:v4.12.0")
    mathlib_rev: str = ""
    allowed_axioms: list[str] = Field(default_factory=lambda: list(STANDARD_AXIOMS))


class LlmJudgeVerifier(BaseModel):
    kind: Literal[VerifierKind.LLM_JUDGE]
    model: str = Field(description="Dated model id, e.g. claude-haiku-4-5-20251001")
    rubric: str = Field(description="Repository-relative path of the rubric")
    temperature: float = 0.0
    samples: int = Field(default=1, ge=1, description="Judgments taken; majority wins")


# ------------------------------------------- the tree under a claim (generic)

T = TypeVar("T", bound=BaseModel)
ParamsT = TypeVar("ParamsT")
ResultT = TypeVar("ResultT")


def active(entries: Sequence[T], id_attr: str) -> list[T]:
    # With append order guaranteed, position carries what a `supersedes`
    # field would: the last entry for an id is the live one.
    latest: dict[str, T] = {}
    for entry in entries:
        latest[getattr(entry, id_attr)] = entry
    return list(latest.values())


class Run(BaseModel, Generic[ParamsT, ResultT]):
    run_id: str = Field(description="Results directory this run produces; repo-unique")
    description: str = ""
    params: ParamsT
    results: list[ResultT] = Field(default_factory=list)

    def latest_result(self) -> ResultT | None:
        return self.results[-1] if self.results else None


RunT = TypeVar("RunT", bound=Run[Any, Any])


class Design(BaseModel, Generic[RunT]):
    id: str = Field(pattern=DESIGN_ID_PATTERN)
    summary: str = ""
    runs: list[RunT] = Field(default_factory=list)
    quoted_passage_ids: list[str] = Field(
        default_factory=list, description="Passage ids the design follows"
    )


DesignT = TypeVar("DesignT", bound=Design[Any])
VerifierT = TypeVar("VerifierT", SeyvalVerifier, LeanVerifier, LlmJudgeVerifier)


class ClaimBase(BaseModel, Generic[VerifierT, DesignT]):
    id: str = Field(pattern=CLAIM_ID_PATTERN)
    statement: str = Field(description="One assertive sentence")
    rationale: str = Field(
        min_length=1,
        description="Why this claim holding is evidence for the hypothesis, "
        "and for which part of it: what makes it a member of the set of "
        "claims whose conjunction is meant to imply the hypothesis",
    )
    verifier: VerifierT
    designs: list[DesignT] = Field(default_factory=list)
    quoted_passage_ids: list[str] = Field(
        default_factory=list, description="Passage ids the claim rests on"
    )
    verified: bool = Field(
        default=False,
        description="Every run under this claim has its verifier's report",
    )
    verdict: Optional[Verdict] = None

    def runs(self) -> list[tuple[DesignT, Run[Any, Any]]]:
        # The one place that knows the shape under a claim; a kind that
        # wants a different shape overrides this.
        return [
            (design, run)
            for design in active(self.designs, "id")
            for run in active(design.runs, "run_id")
        ]


# ------------------------------------------------------------------- seyval


class InputRef(BaseModel):
    path: str = Field(description="Repository-relative path of the inputs file")
    sha256: str


# --------------------------------------------------------------- literature

SOURCE_ID_PATTERN = r"^s[1-9][0-9]*$"
PASSAGE_ID_PATTERN = r"^s[1-9][0-9]*\.p[1-9][0-9]*$"
REPOSITORY_ID_PATTERN = r"^s[1-9][0-9]*\.r[1-9][0-9]*$"
# What the passage states — the role a graph walk filters on. Where it
# appears (prose, a table, a figure caption) is the anchor, kept apart.
PassageNodeType = Literal["claim", "result", "method", "setup", "gap", "definition"]
PassageAnchor = Literal["text", "table", "figure"]
Registry = Literal["doi.org", "arxiv", "git", "airas_records"]


class CitationJudgment(BaseModel):
    text_sha256: str = Field(
        description="Of the citing text, so a rewrite needs a new judgment"
    )
    model: str
    supported: bool
    reason: str = ""


class QuotedPassage(BaseModel):
    """A verbatim passage of a source, the unit a hypothesis or claim cites."""

    # TODO: a table's locator (page, table index, row) and a figure's (bbox,
    # image hash). Today a table passage quotes the row text and a figure
    # passage its caption, both found in the fulltext snapshot.
    id: str = Field(pattern=PASSAGE_ID_PATTERN)
    node_type: PassageNodeType
    anchor: PassageAnchor = "text"
    quote: str = Field(
        min_length=1, description="Verbatim, copied from the fulltext snapshot"
    )
    judgments: list[CitationJudgment] = Field(default_factory=list)


class Repository(BaseModel):
    id: str = Field(pattern=REPOSITORY_ID_PATTERN)
    url: str
    commit: str = Field(pattern=r"^[0-9a-f]{40}$")
    snapshot: Optional[InputRef] = Field(
        default=None,
        description=".research/sources/<source>/<r>.txt: one page per file",
    )
    method_entry: str = Field(
        default="",
        description="module.Class.method whose call runs the method this source holds",
    )


class LiteratureSource(BaseModel):
    id: str = Field(pattern=SOURCE_ID_PATTERN)
    title: str
    authors: list[str] = Field(default_factory=list)
    year: Optional[int] = None
    venue: str = ""
    doi: Optional[str] = None
    arxiv_id: Optional[str] = None
    url: Optional[str] = None
    bibkey: str
    verified_by: Literal["", "doi.org", "arxiv", "git", "airas_records"] = Field(
        default="",
        description="Registry that confirmed the source exists at registration",
    )
    verified_at: str = Field(default="", description="ISO-8601 UTC")
    fulltext: Optional[InputRef] = Field(
        default=None,
        description="The paper's text, .research/sources/<id>/fulltext.txt",
    )
    parser: str = Field(default="", description="e.g. 'pymupdf 1.26.0'")
    repositories: list[Repository] = Field(default_factory=list)
    passages: list[QuotedPassage] = Field(default_factory=list)

    @model_validator(mode="after")
    def _parts_belong_to_this_source(self) -> LiteratureSource:
        parts = [*self.passages, *self.repositories]
        foreign = [p.id for p in parts if not p.id.startswith(f"{self.id}.")]
        if foreign:
            raise ValueError(
                f"source {self.id}: {', '.join(foreign)} carry another source's id"
            )
        ids = [r.id for r in self.repositories]
        if len(set(ids)) != len(ids):
            raise ValueError(f"source {self.id}: repository ids must be unique")
        if self.verified_by in ("git", "airas_records") and not self.repositories:
            raise ValueError(
                f"source {self.id}: {self.verified_by} verifies a repository, "
                "and this source has none"
            )
        return self


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


class SeyvalResult(BaseModel):
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


class SeyvalRun(Run[dict[str, Any], SeyvalResult]):
    params: dict[str, Any] = Field(
        default_factory=dict,
        description="Every condition that can change this run's result: the "
        "dispatch conditions (mode) and every key of config/config.yaml ⊕ "
        "config/run/<run_id>.yaml. Checked against the committed config and "
        "what the platform recorded",
    )


class ArgumentValue(BaseModel):
    argument: str = Field(description="module.Class.method.arg of the upstream")
    value: Any
    reason: str = ""


class RepositoryIntegration(BaseModel):
    """How the design runs the method a source's repository holds: the
    upstream names it extends and the arguments it sets. The upstream files
    themselves are not modified."""

    repository_id: str = Field(
        pattern=REPOSITORY_ID_PATTERN,
        description="Repository whose method_entry this design runs, e.g. 's1.r1'",
    )
    extension_points: list[str] = Field(
        default_factory=list,
        description="Upstream names the adapter may subclass, override or replace",
    )
    arguments: list[ArgumentValue] = Field(default_factory=list)


class SeyvalDesign(Design[SeyvalRun]):
    repository_integration: Optional[RepositoryIntegration] = None


def walk_metric_path(node: Any, path: str) -> float:
    """Get a number from nested metrics using a path like 'a.b.0.c'."""
    for segment in path.split(".") if path else []:
        try:
            node = node[int(segment)] if isinstance(node, list) else node[segment]
        except (KeyError, IndexError, ValueError, TypeError):
            raise ValueError(f"nothing at '{segment}'") from None

    if isinstance(node, bool) or not isinstance(node, (int, float)):
        raise ValueError(f"not a number: {node!r}")

    return float(node)


CriterionOp = Literal[">=", "<=", ">", "<"]


class Criterion(BaseModel):
    """The falsification line: (subject.metric - reference) op margin.

    `reference` is a run id (its same metric is subtracted) or a constant.
    A difference exactly at the margin counts as meeting it.
    """

    metric: str = Field(
        min_length=1, description="Path inside metrics.json, e.g. 'accuracy'"
    )
    subject: str = Field(description="run_id whose metric is judged")
    reference: Union[str, float] = Field(
        description="run_id compared against on the same metric, or a constant"
    )
    op: CriterionOp
    margin: float = 0.0
    quoted_passage_ids: list[str] = Field(
        default_factory=list,
        description="Passages a constant reference was read from, e.g. ['s1.p2']",
    )

    @model_validator(mode="after")
    def _subject_is_not_the_reference(self) -> Criterion:
        if self.subject == self.reference:
            raise ValueError("criterion compares a run to itself")

        if self.quoted_passage_ids and isinstance(self.reference, str):
            raise ValueError(
                "quoted_passage_ids names where a constant reference was read; "
                "this reference is a run"
            )
        return self

    def observed(self, metrics_by_run: Mapping[str, Any]) -> float:
        """The difference the criterion judges; raises when a value is missing."""
        subject = walk_metric_path(metrics_by_run[self.subject], self.metric)
        if isinstance(self.reference, str):
            return subject - walk_metric_path(
                metrics_by_run[self.reference], self.metric
            )
        return subject - self.reference

    def holds(self, difference: float) -> bool:
        at_margin = math.isclose(difference, self.margin, rel_tol=1e-9, abs_tol=1e-12)
        if self.op == ">=":
            return at_margin or difference > self.margin
        if self.op == "<=":
            return at_margin or difference < self.margin
        if self.op == ">":
            return difference > self.margin and not at_margin
        return difference < self.margin and not at_margin


class Prediction(BaseModel):
    """Where the difference is expected to land: a range, never a point."""

    low: float
    high: float
    basis: str = Field(min_length=1, description="Prior work, pilot, ...")

    @model_validator(mode="after")
    def _is_a_range(self) -> Prediction:
        if not self.low < self.high:
            raise ValueError("prediction must be a range with low < high")
        return self


class SeyvalClaim(ClaimBase[SeyvalVerifier, SeyvalDesign]):
    criterion: Criterion = Field(
        description="Frozen at declaration; the verdict derives from it"
    )
    prediction: Prediction = Field(
        description="Predicted interval for the criterion's difference"
    )


# --------------------------------------------------------------------- lean


class LeanParams(BaseModel):
    module: str = Field(description="Lean module to build, e.g. Airas.Thm1")
    decl: str = Field(description="The declaration that is the claim")
    statement: str = Field(description="Its type, as `#check @decl` prints it")


class LeanResult(BaseModel):
    id: str = Field(
        default="", description="The backend's execution id, from the manifest"
    )
    commit: Optional[str] = None
    toolchain: str = Field(default="", description="What built it, per the report")
    mathlib_rev: str = ""
    statement: str = Field(default="", description="The built declaration's type")
    statement_matches: Optional[bool] = Field(
        default=None,
        description=(
            "Whether the declared statement, elaborated by the report tool, is "
            "the built type as a term; None when the report carried no "
            "comparison, which is an error"
        ),
    )
    axioms: list[str] = Field(default_factory=list)
    # A failed build is a result too. Any entry here makes the verdict
    # inconclusive: a proof that did not go through proves nothing either way.
    errors: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)


LeanRun = Run[LeanParams, LeanResult]
LeanDesign = Design[LeanRun]


class LeanClaim(ClaimBase[LeanVerifier, LeanDesign]):
    pass


# ---------------------------------------------------------------- llm_judge


class LlmJudgeParams(BaseModel):
    evidence: list[str] = Field(description="Repository-relative paths judged")


class LlmJudgeResult(BaseModel):
    id: str = Field(default="", description="The provider's id for the first response")
    commit: Optional[str] = None
    inputs_sha256: str = Field(description="rubric + evidence + statement + model")
    verdict: Verdict
    errors: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)


LlmJudgeRun = Run[LlmJudgeParams, LlmJudgeResult]
LlmJudgeDesign = Design[LlmJudgeRun]


class LlmJudgeClaim(ClaimBase[LlmJudgeVerifier, LlmJudgeDesign]):
    pass


# ---------------------------------------------- the claim: one tag, one type


def claim_kind(value: Any) -> str | None:
    # The union's tag is the claim's verifier.kind; None (absent) is rejected.
    verifier = (
        value.get("verifier")
        if isinstance(value, dict)
        else getattr(value, "verifier", None)
    )
    kind = (
        verifier.get("kind")
        if isinstance(verifier, dict)
        else getattr(verifier, "kind", None)
    )
    return str(kind) if kind is not None else None


ClaimDeclaration = Annotated[
    Union[
        Annotated[SeyvalClaim, Tag(VerifierKind.SEYVAL)],
        Annotated[LeanClaim, Tag(VerifierKind.LEAN)],
        Annotated[LlmJudgeClaim, Tag(VerifierKind.LLM_JUDGE)],
    ],
    Discriminator(claim_kind),
]

AnyRun = Run[Any, Any]
AnyDesign = Design[Any]
RunResult = Union[SeyvalResult, LeanResult, LlmJudgeResult]


# --------------------------------------------------------- hypothesis, record


class RenderedChart(BaseModel):
    renderer: str = Field(description="e.g. 'vl-convert-python 1.7.0'")


class ChartDeclaration(BaseModel):
    path: str = Field(description="Chart path relative to .research/results/chart/")
    format: Literal["svg", "png"]
    spec: dict[str, Any] = Field(
        description="Unresolved Vega-Lite spec; data points are 'metric:' refs"
    )
    renders: list[RenderedChart] = Field(default_factory=list)


class Hypothesis(BaseModel):
    id: str = Field(pattern=HYPOTHESIS_ID_PATTERN)
    statement: str = Field(description="The hypothesis itself, in prose")
    assumptions: list[str] = Field(
        default_factory=list,
        description="What must be granted for the claims together to imply "
        "the hypothesis — the bridge from c1 ∧ … ∧ cn to H, each naming the "
        "claims it concerns. Every claim supported leaves exactly these "
        "unverified",
    )
    quoted_passage_ids: list[str] = Field(
        default_factory=list,
        description="Passage ids that motivated the hypothesis — the gap it "
        "answers, in the prior work's own words",
    )
    claims: list[ClaimDeclaration] = Field(default_factory=list)
    tables: list[TableSpec] = Field(default_factory=list)
    charts: list[ChartDeclaration] = Field(default_factory=list)
    notes: list[str] = Field(default_factory=list)


class ResearchRecord(BaseModel):
    literature: list[LiteratureSource] = Field(default_factory=list)
    hypotheses: list[Hypothesis] = Field(default_factory=list)

    def save(self, local_repo_path: str) -> Path:
        path = record_path(local_repo_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        # Defaults are omitted so the file reads as what was declared;
        # containment compares model dumps, not text.
        path.write_text(
            self.model_dump_json(indent=2, exclude_defaults=True) + "\n",
            encoding="utf-8",
        )
        return path

    def active_literature(self) -> list[LiteratureSource]:
        return active(self.literature, "id")

    def passage_index(self) -> dict[str, tuple[LiteratureSource, QuotedPassage]]:
        return {
            passage.id: (source, passage)
            for source in self.active_literature()
            for passage in active(source.passages, "id")
        }

    def active_hypotheses(self) -> list[Hypothesis]:
        return active(self.hypotheses, "id")

    def active_claims(self) -> Iterator[tuple[Hypothesis, ClaimDeclaration]]:
        for hypothesis in self.active_hypotheses():
            for claim in active(hypothesis.claims, "id"):
                yield hypothesis, claim

    def active_runs(
        self,
    ) -> Iterator[tuple[Hypothesis, ClaimDeclaration, AnyDesign, AnyRun]]:
        for hypothesis, claim in self.active_claims():
            for design, run in claim.runs():
                yield hypothesis, claim, design, run

    def run_index(self) -> dict[str, AnyRun]:
        return {run.run_id: run for _, _, _, run in self.active_runs()}

    def claim_index(self) -> dict[str, ClaimDeclaration]:
        return {claim.id: claim for _, claim in self.active_claims()}

    def active_tables(self) -> list[TableSpec]:
        return [t for h in self.active_hypotheses() for t in active(h.tables, "key")]

    def active_charts(self) -> list[ChartDeclaration]:
        return [c for h in self.active_hypotheses() for c in active(h.charts, "path")]
