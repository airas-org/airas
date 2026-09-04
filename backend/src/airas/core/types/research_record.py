from __future__ import annotations

from enum import StrEnum
from typing import (
    Annotated,
    Any,
    Generic,
    Iterator,
    Literal,
    Optional,
    Sequence,
    TypeVar,
    Union,
)

from pydantic import BaseModel, Discriminator, Field, Tag

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


DesignT = TypeVar("DesignT", bound=Design[Any])
VerifierT = TypeVar("VerifierT", SeyvalVerifier, LeanVerifier, LlmJudgeVerifier)


class ClaimBase(BaseModel, Generic[VerifierT, DesignT]):
    id: str = Field(pattern=CLAIM_ID_PATTERN)
    statement: str = Field(description="One assertive sentence")
    verifier: VerifierT
    designs: list[DesignT] = Field(default_factory=list)
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
        description="Conditions this run is declared to be dispatched with, "
        "e.g. {'mode': 'full'}. Checked against what the platform recorded",
    )


SeyvalDesign = Design[SeyvalRun]


class SeyvalClaim(ClaimBase[SeyvalVerifier, SeyvalDesign]):
    pass


# --------------------------------------------------------------------- lean


class LeanParams(BaseModel):
    module: str = Field(description="Lean module to build, e.g. Airas.Thm1")
    decl: str = Field(description="The declaration that is the claim")
    statement: str = Field(description="Its type, as `#check @decl` prints it")


class LeanResult(BaseModel):
    commit: Optional[str] = None
    statement: str = Field(default="", description="The built declaration's type")
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
    claims: list[ClaimDeclaration] = Field(default_factory=list)
    tables: list[TableSpec] = Field(default_factory=list)
    charts: list[ChartDeclaration] = Field(default_factory=list)
    notes: list[str] = Field(default_factory=list)


class ResearchRecord(BaseModel):
    hypotheses: list[Hypothesis] = Field(default_factory=list)

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
