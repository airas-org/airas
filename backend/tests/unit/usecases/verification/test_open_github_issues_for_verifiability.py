"""A model proposes changes that would make unverified declarations verifiable;
only the verifiable proposals become GitHub issues, at most five, never one
whose title is already open."""

import asyncio
import subprocess
from pathlib import Path
from typing import Any

import pytest

from airas.core.types.research_record import (
    Criterion,
    Hypothesis,
    Prediction,
    ResearchRecord,
    SeyvalClaim,
    SeyvalDesign,
    SeyvalResult,
    SeyvalRun,
    SeyvalVerifier,
    VerifierKind,
)
from airas.usecases.verification.open_github_issues_for_verifiability import (
    _DOCUMENT_BYTES,
    VerifiabilityProposal,
    _document,
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


def _repo(tmp_path: Path, run_id: str = "proposed") -> Path:
    claim = SeyvalClaim(
        id="c1",
        statement="proposed beats baseline",
        rationale="the direct comparison",
        verifier=SeyvalVerifier(kind=VerifierKind.SEYVAL),
        criterion=Criterion(
            metric="acc", subject=run_id, reference="baseline", op=">="
        ),
        prediction=Prediction(low=0.01, high=0.05, basis="prior work"),
        designs=[
            SeyvalDesign(
                id="d1",
                summary="rate laws limited to three kinds",
                runs=[
                    SeyvalRun(
                        run_id=run_id,
                        results=[SeyvalResult(verifier="seyval", id="x", metrics={})],
                    ),
                    SeyvalRun(run_id="baseline"),
                ],
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
    git = ["git", "-C", str(tmp_path)]
    subprocess.run([*git, "init", "-q"], check=True)
    subprocess.run([*git, "config", "user.email", "t@example.com"], check=True)
    subprocess.run([*git, "config", "user.name", "t"], check=True)
    subprocess.run([*git, "add", "."], check=True)
    subprocess.run([*git, "commit", "-q", "-m", "record"], check=True)
    subprocess.run(
        [*git, "remote", "add", "origin", "git@github.com:o/r.git"], check=True
    )
    return tmp_path


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
            model="judge-1",
            litellm_client=model,
            github_client=_GitHub([]),
            store_factory=lambda backend, url: pytest.fail("no store in this test"),
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
            model="judge-1",
            litellm_client=_Model(proposals),
            github_client=github,
            store_factory=lambda backend, url: pytest.fail("no store in this test"),
        )
    )
    assert returned == proposals
    assert [t for _, _, t, _ in github.created] == [
        f"verifiable: proposal {n}" for n in range(1, 6)
    ]
    assert len(urls) == 5 and all(u.startswith("https://github.com/o/r/") for u in urls)
    assert github.created[0][3].startswith("change 1")


def test_nothing_outside_the_checkout_is_read(tmp_path: Path) -> None:
    secret = tmp_path / "secret.txt"
    secret.write_text("SECRET-OUTSIDE")
    root = _repo(tmp_path / "repo", run_id="../../../outside")
    (root / "src/link.py").symlink_to(secret)
    outside = tmp_path / "outside"
    outside.mkdir()
    (outside / "observed.json").write_text("SECRET-OBSERVED")
    model = _Model([])
    asyncio.run(
        open_github_issues_for_verifiability(
            str(root),
            model="judge-1",
            litellm_client=model,
            github_client=_GitHub([]),
            store_factory=lambda backend, url: pytest.fail("no store in this test"),
        )
    )
    assert "SECRET" not in model.messages[0]


def test_a_document_is_cut_at_the_byte_limit_not_the_character_count() -> None:
    cut = _document("あ" * _DOCUMENT_BYTES)
    assert cut.endswith("(truncated)")
    assert len(cut.encode("utf-8")) <= _DOCUMENT_BYTES + len("\n(truncated)")


def test_issues_need_a_head_commit_to_link_to(tmp_path: Path) -> None:
    root = _repo(tmp_path)
    subprocess.run(
        ["git", "-C", str(root), "update-ref", "-d", "refs/heads/master"],
        check=False,
    )
    subprocess.run(
        ["git", "-C", str(root), "update-ref", "-d", "refs/heads/main"], check=False
    )
    github = _GitHub([])
    with pytest.raises(ValueError, match="no HEAD commit"):
        asyncio.run(
            open_github_issues_for_verifiability(
                str(root),
                model="judge-1",
                litellm_client=_Model([_proposal(1)]),
                github_client=github,
                store_factory=lambda backend, url: pytest.fail("no store in this test"),
            )
        )
    assert github.created == []
