"""A design's code and runs, read by a model against the design."""

import hashlib
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
from airas.research_record.verify._verify_implementation import verify_implementation

ADAPTER_PY = "KINDS = ['mass_action', 'michaelis_menten', 'hill']\n"


def _git(root: Path, *args: str) -> str:
    return subprocess.run(
        ["git", "-C", str(root), *args], check=True, capture_output=True, text=True
    ).stdout.strip()


def _repo(tmp_path: Path) -> tuple[Path, str]:
    (tmp_path / "src").mkdir()
    (tmp_path / "src/adapter.py").write_text(ADAPTER_PY)
    (tmp_path / "config").mkdir()
    (tmp_path / "config/config.yaml").write_text("budget: 20\n")
    _git(tmp_path, "init", "-q")
    _git(tmp_path, "config", "user.email", "t@example.com")
    _git(tmp_path, "config", "user.name", "t")
    _git(tmp_path, "add", ".")
    _git(tmp_path, "commit", "-q", "-m", "code")
    return tmp_path, _git(tmp_path, "rev-parse", "HEAD")


def _observed(
    root: Path, run_id: str, text: str = '{"version": 3, "calls": {}}'
) -> str:
    path = root / ".research/results" / run_id / "observed.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text)
    return hashlib.sha256(text.encode()).hexdigest()


def _record(commit: str) -> ResearchRecord:
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
        hypotheses=[
            Hypothesis(
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
                                runs=[
                                    SeyvalRun(
                                        run_id="run-1",
                                        results=[
                                            SeyvalResult(
                                                verifier="seyval",
                                                id="x1",
                                                commit=commit,
                                                metrics={"m": 1.0},
                                            )
                                        ],
                                    )
                                ],
                            )
                        ],
                    )
                ],
            )
        ],
    )


class _Judge:
    """Stands in for the model: returns `findings`, keeps the prompts it saw."""

    def __init__(self, findings: list[ReviewFinding]) -> None:
        self.findings = findings
        self.prompts: list[str] = []

    async def structured_output(
        self, llm_name: str, message: str, data_model: Any, **_: Any
    ) -> Any:
        self.prompts.append(message)
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


async def _verify(
    root: Path, record: ResearchRecord, judge: _Judge | None = None
) -> tuple[list[str], list[str], int]:
    return await verify_implementation(
        root, record, model="judge-1" if judge else None, litellm_client=judge
    )


async def test_without_a_model_an_unreviewed_design_fails(tmp_path: Path) -> None:
    root, commit = _repo(tmp_path)
    _observed(root, "run-1")
    problems, reports, reviewed = await _verify(root, _record(commit))
    assert reviewed == 0 and reports == []
    assert problems == [
        f"design d1: no implementation review covers commit {commit[:12]} and its runs' "
        "observed.json (verify with a model to write one)"
    ]


async def test_a_model_reads_the_design_once_and_its_findings_are_kept(
    tmp_path: Path,
) -> None:
    root, commit = _repo(tmp_path)
    sha = _observed(root, "run-1")
    record = _record(commit)
    judge = _Judge(FINDINGS)
    problems, reports, reviewed = await _verify(root, record, judge)
    assert reviewed == 1 and len(judge.prompts) == 1
    prompt = judge.prompts[0]
    assert ADAPTER_PY in prompt and "budget: 20" in prompt  # the code at the commit
    assert "[s1.p1] the LLM writes free-form rate laws" in prompt  # the cited passages
    assert (
        "速度則は質量作用か MM" in prompt and '"version": 3' in prompt
    )  # the declaration and the run
    review = record.hypotheses[0].claims[0].designs[0].reviews[0]
    assert review == ImplementationReview(
        commit=commit, observed={"run-1": sha}, model="judge-1", findings=FINDINGS
    )
    assert problems == [
        "design d1: contradiction: 宣言は 2 型、コードは Hill を含む 3 型 (src/adapter.py:1 KINDS) [judge-1]"
    ]
    assert reports == [
        "design d1: undeclared: budget が 20 に固定 (config/config.yaml:1)"
    ]
    # the recorded review serves the gate without a model, and is not read again
    again = await _verify(root, record)
    assert again == (problems, reports, 0)
    assert len(judge.prompts) == 1


async def test_a_rerun_or_a_code_change_needs_a_new_review(tmp_path: Path) -> None:
    root, commit = _repo(tmp_path)
    _observed(root, "run-1")
    record = _record(commit)
    await _verify(root, record, _Judge([]))
    _observed(root, "run-1", '{"version": 3, "calls": {"src.adapter.f": {}}}')
    problems, _, _ = await _verify(root, record)
    assert problems and "no implementation review covers" in problems[0]


async def test_runs_produced_by_different_code_cannot_be_reviewed_together(
    tmp_path: Path,
) -> None:
    root, commit = _repo(tmp_path)
    (root / "src/adapter.py").write_text(ADAPTER_PY + "# v2\n")
    _git(root, "commit", "-q", "-am", "edit")
    other = _git(root, "rev-parse", "HEAD")
    record = _record(commit)
    design = record.hypotheses[0].claims[0].designs[0]
    design.runs.append(
        SeyvalRun(
            run_id="run-2",
            results=[
                SeyvalResult(
                    verifier="seyval", id="x2", commit=other, metrics={"m": 1.0}
                )
            ],
        )
    )
    _observed(root, "run-1")
    _observed(root, "run-2")
    problems, _, reviewed = await _verify(root, record, _Judge([]))
    assert reviewed == 0 and len(problems) == 1
    assert problems[0].startswith(
        "design d1: its runs' latest results are at different commits"
    )
