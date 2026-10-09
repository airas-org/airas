"""One run's code and observation, read by a model against its declaration on
the platform; the gate reads the review back from the run's results."""

import hashlib
import json
import subprocess
from pathlib import Path
from typing import Any

from airas.core.types.research_record import (
    Criterion,
    Hypothesis,
    ImplementationReview,
    LiteratureSource,
    Prediction,
    QuotedPassage,
    Repository,
    RepositoryIntegration,
    ResearchRecord,
    ReviewFinding,
    SeyvalClaim,
    SeyvalDesign,
    SeyvalResult,
    SeyvalRun,
    SeyvalVerifier,
    VerifierKind,
)
from airas.research_record.verify.implementation_review import (
    review_implementation,
    verify_implementation,
)
from airas.research_record.verify.verify_record import verify_record

ADAPTER_PY = "KINDS = ['mass_action', 'michaelis_menten', 'hill']\n"
OBSERVED = '{"version": 3, "calls": {}}'


def _git(root: Path, *args: str) -> str:
    return subprocess.run(
        ["git", "-C", str(root), *args], check=True, capture_output=True, text=True
    ).stdout.strip()


def _commit_all(root: Path, message: str) -> str:
    _git(root, "add", "-A")
    _git(root, "commit", "-q", "-m", message)
    return _git(root, "rev-parse", "HEAD")


def _repo(
    tmp_path: Path, declared: ResearchRecord | dict[str, Any] | None
) -> tuple[Path, str]:
    """A repository holding the code and, at its commit, the record (or the
    design before the freeze)."""
    (tmp_path / "src").mkdir()
    (tmp_path / "src/adapter.py").write_text(ADAPTER_PY)
    (tmp_path / "config").mkdir()
    (tmp_path / "config/config.yaml").write_text("budget: 20\n")
    _git(tmp_path, "init", "-q")
    _git(tmp_path, "config", "user.email", "t@example.com")
    _git(tmp_path, "config", "user.name", "t")
    if isinstance(declared, ResearchRecord):
        declared.save(str(tmp_path))
    elif declared is not None:
        (tmp_path / ".research").mkdir(exist_ok=True)
        (tmp_path / ".research/design.json").write_text(json.dumps(declared))
    return tmp_path, _commit_all(tmp_path, "code")


def _observed(root: Path, run_id: str, text: str = OBSERVED) -> str:
    path = root / ".research/results" / run_id / "observed.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text)
    return hashlib.sha256(text.encode()).hexdigest()


def _hypothesis(results: list[SeyvalResult]) -> Hypothesis:
    return Hypothesis(
        id="h1",
        statement="h",
        notes=["速度則は質量作用か MM"],
        quoted_passage_ids=["s1.p1"],
        claims=[
            SeyvalClaim(
                verifier=SeyvalVerifier(kind=VerifierKind.SEYVAL),
                id="c1",
                statement="s",
                rationale="r",
                criterion=Criterion(
                    metric="m", subject="run-1", reference=0.0, op=">="
                ),
                prediction=Prediction(low=0.0, high=1.0, basis="b"),
                designs=[
                    SeyvalDesign(
                        id="d1",
                        summary="質量作用または MM の速度則で候補を作る",
                        repository_integration=RepositoryIntegration(
                            repository_id="s1.r1"
                        ),
                        runs=[SeyvalRun(run_id="run-1", results=results)],
                    )
                ],
            )
        ],
    )


def _record(results: list[SeyvalResult] | None = None) -> ResearchRecord:
    return ResearchRecord(
        literature=[
            LiteratureSource(
                id="s1",
                title="paper",
                bibkey="paper-2026",
                verified_by="arxiv",
                passages=[
                    QuotedPassage(
                        id="s1.p1",
                        node_type="method",
                        quote="the LLM writes free-form rate laws",
                    )
                ],
                repositories=[
                    Repository(
                        id="s1.r1",
                        url="https://github.com/acme/pkg",
                        commit="a" * 40,
                        method_entry="pkg.Runner.run",
                    )
                ],
            )
        ],
        hypotheses=[_hypothesis(results or [])],
    )


def _result(commit: str) -> SeyvalResult:
    return SeyvalResult(verifier="seyval", id="x1", commit=commit, metrics={"m": 1.0})


class _Judge:
    """Stands in for the model: returns `findings`, keeps what it was sent."""

    def __init__(self, findings: list[ReviewFinding]) -> None:
        self.findings = findings
        self.prompts: list[str] = []
        self.system = ""

    async def structured_output(
        self, llm_name: str, message: str, data_model: Any, system: str = "", **_: Any
    ) -> Any:
        self.prompts.append(message)
        self.system = system
        return data_model(findings=self.findings)


FINDINGS = [
    ReviewFinding(
        kind="contradiction",
        where="src/adapter.py:1 KINDS",
        statement="宣言は 2 型、コードは Hill を含む 3 型",
        evidence="KINDS = ['mass_action', 'michaelis_menten', 'hill']",
    ),
    ReviewFinding(
        kind="undeclared", where="config/config.yaml:1", statement="budget が 20 に固定"
    ),
]
PROBLEM = (
    "run 'run-1': contradiction: 宣言は 2 型、コードは Hill を含む 3 型 (src/adapter.py:1 KINDS) "
    "[judge-1]"
)
REPORT = "run 'run-1': undeclared: budget が 20 に固定 (config/config.yaml:1)"


async def _review(root: Path, commit: str, judge: _Judge) -> ImplementationReview | str:
    return await review_implementation(
        root,
        "run-1",
        commit,
        model="judge-1",
        litellm_client=judge,
    )


async def test_the_platform_writes_the_review_into_the_run_results(
    tmp_path: Path,
) -> None:
    root, commit = _repo(tmp_path, _record())
    sha = _observed(root, "run-1")
    judge = _Judge(FINDINGS)
    review = await _review(root, commit, judge)
    assert isinstance(review, ImplementationReview)
    prompt = judge.prompts[0]
    assert ADAPTER_PY in prompt and "budget: 20" in prompt  # the code at the commit
    assert "[s1.p1] the LLM writes free-form rate laws" in prompt  # the cited passages
    assert (
        "速度則は質量作用か MM" in prompt and '"version": 3' in prompt
    )  # declaration, run
    assert (
        "undeclared" in judge.system and "undeclared" not in prompt
    )  # rules apart from data
    assert review.design_id == "d1" and review.commit == commit
    assert review.observed_sha256 == sha and review.findings == FINDINGS
    written = ImplementationReview.model_validate_json(
        (root / ".research/results/run-1/implementation_review.json").read_text()
    )
    assert written == review


async def test_before_the_freeze_the_design_file_is_the_declaration(
    tmp_path: Path,
) -> None:
    design = {
        "literature": [
            {
                "title": "paper",
                "passages": [
                    {
                        "node_type": "method",
                        "quote": "the LLM writes free-form rate laws",
                    }
                ],
                "repositories": [
                    {
                        "url": "https://github.com/acme/pkg",
                        "commit": "a" * 40,
                        "method_entry": "pkg.Runner.run",
                    }
                ],
            }
        ],
        "hypotheses": [_hypothesis([]).model_dump(mode="json")],
    }
    root, commit = _repo(tmp_path, design)
    _observed(root, "run-1")
    judge = _Judge([])
    review = await _review(root, commit, judge)
    assert isinstance(review, ImplementationReview)
    assert "[s1.p1] the LLM writes free-form rate laws" in judge.prompts[0]
    assert (
        '"id": "s1.r1"' in judge.prompts[0]
    )  # ids as preregistration will assign them
    # the frozen record declares the same design: the gate accepts this review
    assert (
        review.declaration_sha256
        == (await _review(root, commit, judge)).declaration_sha256
    )


async def test_an_undeclared_run_is_not_reviewed(tmp_path: Path) -> None:
    root, commit = _repo(tmp_path, None)
    _observed(root, "run-1")
    judge = _Judge(FINDINGS)
    outcome = await _review(root, commit, judge)
    assert isinstance(outcome, str) and "is declared neither" in outcome
    assert judge.prompts == []
    assert not (root / ".research/results/run-1/implementation_review.json").exists()
    assert "left no observed.json" in str(
        await review_implementation(
            root,
            "run-2",
            commit,
            model="judge-1",
            litellm_client=judge,
        )
    )


async def test_the_gate_reads_the_review_back(tmp_path: Path) -> None:
    root, commit = _repo(tmp_path, _record())
    _observed(root, "run-1")
    await _review(root, commit, _Judge(FINDINGS))
    record = _record([_result(commit)])
    assert verify_implementation(root, record) == ([PROBLEM], [REPORT])


async def test_the_gate_needs_a_review_of_this_run_this_code_and_this_declaration(
    tmp_path: Path,
) -> None:
    root, commit = _repo(tmp_path, _record())
    _observed(root, "run-1")
    record = _record([_result(commit)])
    problems, reports = verify_implementation(root, record)
    assert reports == [] and len(problems) == 1
    assert "no implementation_review.json among its results" in problems[0]

    await _review(root, commit, _Judge([]))
    assert verify_implementation(root, record) == ([], [])

    _observed(
        root, "run-1", '{"version": 3, "calls": {"src.adapter.f": {}}}'
    )  # a rerun
    problems, _ = verify_implementation(root, record)
    assert problems == ["run 'run-1': the review read a different observed.json"]

    _observed(root, "run-1")
    record.hypotheses[0].claims[0].designs[
        0
    ].summary += "。Hill も使う"  # declared again
    problems, _ = verify_implementation(root, record)
    assert problems == [
        "run 'run-1': design d1 was declared again after the review read it; the run must be repeated"
    ]

    record = _record([_result(commit)])
    record.hypotheses[0].notes.append(
        "分析: 反応数は 12 まで"
    )  # notes may follow the run
    assert verify_implementation(root, record) == ([], [])

    record = _record([_result("f" * 40)])
    problems, _ = verify_implementation(root, record)
    assert problems == [
        f"run 'run-1': the review read commit {commit[:12]}, not the result's {'f' * 40}"
    ]


async def test_a_seyval_run_without_a_review_is_reported_not_failed(
    tmp_path: Path,
) -> None:
    root, commit = _repo(tmp_path, _record())
    _observed(root, "run-1")
    (root / ".research/results/.provenance.json").write_text(
        json.dumps(
            {
                "dirs": {
                    "run-1": {
                        "execution_id": "e1",
                        "backend": "seyval",
                        "commit_hash": commit,
                    }
                }
            }
        )
    )
    problems, reports = verify_implementation(root, _record([_result(commit)]))
    assert problems == [] and reports == [
        "run 'run-1': not reviewed (Seyval runs have no review step yet)"
    ]


async def test_the_record_gate_surfaces_the_review(tmp_path: Path) -> None:
    root, commit = _repo(tmp_path, _record())
    _observed(root, "run-1")
    (root / ".research/results/run-1/metrics.json").write_text('{"m": 1.0}')
    await _review(root, commit, _Judge(FINDINGS))
    _record([_result(commit)]).save(str(root))
    result = await verify_record(
        str(root), check_provenance=False, require_history=False
    )
    assert result.reports == [REPORT] and PROBLEM in result.problems
