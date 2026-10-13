"""A model proposes changes that would make unverified declarations verifiable;
only the verifiable proposals become GitHub issues, at most five, never one
whose title is already open."""

import asyncio
import subprocess
from pathlib import Path
from typing import Any

from airas.core.types.record_verification import RecordVerification
from airas.core.types.research_record import (
    Criterion,
    Hypothesis,
    Prediction,
    ResearchRecord,
    SeyvalClaim,
    SeyvalDesign,
    SeyvalRun,
    SeyvalVerifier,
    VerifierKind,
)
from airas.usecases.verification.open_github_issues_for_verifiability import (
    VerifiabilityProposal,
    open_github_issues_for_verifiability,
)


class _Model:
    def __init__(self, proposals: list[VerifiabilityProposal]) -> None:
        self.proposals = proposals
        self.messages: list[str] = []
        self.system = ""

    async def structured_output(
        self, llm_name: str, message: str, data_model: Any, system: str = "", **_: Any
    ) -> Any:
        self.messages.append(message)
        self.system = system
        return data_model(proposals=self.proposals)


class _GitHub:
    def __init__(self, open_titles: list[str]) -> None:
        self.open_titles = open_titles
        self.created: list[tuple[str, str, str, str]] = []

    async def alist_open_issue_titles(self, owner: str, name: str) -> list[str]:
        return self.open_titles

    async def acreate_issue(self, owner: str, name: str, title: str, body: str) -> str:
        self.created.append((owner, name, title, body))
        return f"https://github.com/{owner}/{name}/issues/{len(self.created)}"


def _repo(tmp_path: Path) -> Path:
    claim = SeyvalClaim(
        id="c1",
        statement="proposed beats baseline",
        rationale="the direct comparison",
        verifier=SeyvalVerifier(kind=VerifierKind.SEYVAL),
        criterion=Criterion(
            metric="acc", subject="proposed", reference="baseline", op=">="
        ),
        prediction=Prediction(low=0.01, high=0.05, basis="prior work"),
        designs=[
            SeyvalDesign(
                id="d1",
                summary="rate laws limited to three kinds",
                runs=[SeyvalRun(run_id="proposed"), SeyvalRun(run_id="baseline")],
            )
        ],
    )
    ResearchRecord(
        hypotheses=[
            Hypothesis(id="h1", statement="regularization helps", claims=[claim])
        ]
    ).save(str(tmp_path))
    (tmp_path / "src").mkdir()
    (tmp_path / "src/adapter.py").write_text("KINDS = ['mass_action', 'hill']\n")
    subprocess.run(["git", "-C", str(tmp_path), "init", "-q"], check=True)
    subprocess.run(
        [
            "git",
            "-C",
            str(tmp_path),
            "remote",
            "add",
            "origin",
            "git@github.com:o/r.git",
        ],
        check=True,
    )
    return tmp_path


def _verification() -> RecordVerification:
    verification = RecordVerification(stage="prereg")
    verification.append_declaration_status(
        "hypotheses[h1]/claims[c1]/designs[d1]/summary", "no check", "unverified"
    )
    verification.append_declaration_status(
        "hypotheses[h1]/claims[c1]/criterion",
        "subject 'proposed' among this claim's runs",
        "verified",
    )
    return verification


def _proposal(n: int, verifiable: bool = True) -> VerifiabilityProposal:
    return VerifiabilityProposal(
        title=f"proposal {n}", change=f"change {n}", verifiable=verifiable
    )


def test_the_model_reads_the_unverified_rows_the_record_and_the_code(
    tmp_path: Path,
) -> None:
    root = _repo(tmp_path)
    model = _Model([])
    proposals, urls = asyncio.run(
        open_github_issues_for_verifiability(
            str(root),
            _verification(),
            model="judge-1",
            litellm_client=model,
            github_client=_GitHub([]),
        )
    )
    assert proposals == [] and urls == []
    message = model.messages[0]
    assert "=== unverified ===" in message and '"no check"' in message
    assert "rate laws limited to three kinds" in message
    assert "=== src/adapter.py ===" in message and "KINDS" in message
    assert "What the gate compares today" in model.system


def test_only_verifiable_proposals_become_issues_at_most_five_and_never_twice(
    tmp_path: Path,
) -> None:
    root = _repo(tmp_path)
    proposals = [_proposal(n) for n in range(7)] + [_proposal(7, verifiable=False)]
    github = _GitHub(open_titles=["verifiable: proposal 0"])
    returned, urls = asyncio.run(
        open_github_issues_for_verifiability(
            str(root),
            _verification(),
            model="judge-1",
            litellm_client=_Model(proposals),
            github_client=github,
        )
    )
    assert returned == proposals
    assert [t for _, _, t, _ in github.created] == [
        f"verifiable: proposal {n}" for n in range(1, 6)
    ]
    assert len(urls) == 5 and all(u.startswith("https://github.com/o/r/") for u in urls)
    assert github.created[0][3].startswith("change 1")
