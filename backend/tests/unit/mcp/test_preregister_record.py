"""preregister_record initialises the empty record a repository ships in
place, and still refuses to overwrite declarations."""

import subprocess
from pathlib import Path
from typing import Any

import pytest

from airas.core.research_paths import RECORD_PATH
from airas.core.types.research_record import (
    Criterion,
    Hypothesis,
    Prediction,
    SeyvalClaim,
    SeyvalDesign,
    SeyvalRun,
    SeyvalVerifier,
    VerifierKind,
)
from airas.mcp import server
from airas.usecases.recording.update_or_load_record import load_record


def _git(repo: Path, *args: str) -> str:
    return subprocess.run(
        ["git", "-C", str(repo), *args], capture_output=True, text=True, check=True
    ).stdout.strip()


def _repo_with_record(tmp_path: Path, record_json: str) -> Path:
    _git(tmp_path, "init", "-q")
    _git(tmp_path, "config", "user.email", "test@example.com")
    _git(tmp_path, "config", "user.name", "test")
    (tmp_path / RECORD_PATH).parent.mkdir(parents=True)
    (tmp_path / RECORD_PATH).write_text(record_json)
    _git(tmp_path, "add", "-A")
    _git(tmp_path, "commit", "-q", "-m", "template")
    return tmp_path


def _hypotheses() -> list[dict[str, Any]]:
    return [
        Hypothesis(
            id="h1",
            statement="The proposed method beats the baseline.",
            claims=[
                SeyvalClaim(
                    verifier=SeyvalVerifier(kind=VerifierKind.SEYVAL),
                    id="c1",
                    statement="Proposed beats baseline on accuracy.",
                    rationale="Head-to-head on the hypothesis's own metric.",
                    criterion=Criterion(
                        metric="accuracy",
                        subject="proposed",
                        reference="baseline",
                        op=">=",
                        margin=0.02,
                    ),
                    prediction=Prediction(low=0.02, high=0.04, basis="pilot"),
                    designs=[
                        SeyvalDesign(
                            id="d1",
                            summary="Head-to-head on one dataset.",
                            runs=[
                                SeyvalRun(run_id="proposed"),
                                SeyvalRun(run_id="baseline"),
                            ],
                        )
                    ],
                )
            ],
        ).model_dump(mode="json")
    ]


async def test_the_shipped_empty_record_is_initialised_in_place(tmp_path: Path) -> None:
    repo = _repo_with_record(tmp_path, "{}")

    result = await server.preregister_record(str(repo), _hypotheses(), "mdpi")

    assert result["record_path"] == str(repo / RECORD_PATH)
    assert [h.id for h in load_record(str(repo)).hypotheses] == ["h1"]
    assert _git(repo, "rev-list", "--count", "HEAD") == "2"  # the freeze commit


async def test_a_record_that_already_declares_is_not_overwritten(
    tmp_path: Path,
) -> None:
    declared = server.ResearchRecord(
        hypotheses=[Hypothesis.model_validate(h) for h in _hypotheses()]
    )
    repo = _repo_with_record(tmp_path, declared.model_dump_json())

    with pytest.raises(ValueError, match="already holds declarations"):
        await server.preregister_record(str(repo), _hypotheses(), "mdpi")
