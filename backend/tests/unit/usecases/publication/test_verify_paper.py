from pathlib import Path

import pytest

from airas.core.types.research_record import (
    Hypothesis,
    LeanClaim,
    LeanDesign,
    LeanParams,
    LeanRun,
    LeanVerifier,
    ResearchRecord,
    VerifierKind,
)
from airas.research_record.render.render_claims_tex import render_claims_tex
from airas.research_record.verify.verify_paper import verify_paper


@pytest.mark.parametrize("contents", [None, "{", '{"hypotheses": "invalid"}'])
async def test_a_missing_or_invalid_record_fails_paper_verification(
    tmp_path: Path, contents: str | None
) -> None:
    if contents is not None:
        path = tmp_path / ".research" / "record.json"
        path.parent.mkdir()
        path.write_text(contents)
    result = await verify_paper(str(tmp_path), "mdpi")
    assert not result.ok
    assert result.problems


async def test_lean_outputs_require_values_tex_without_experimental_metrics(
    tmp_path: Path,
) -> None:
    run = LeanRun(
        run_id="proof",
        params=LeanParams(module="Airas.Proof", decl="theorem1", statement="True"),
    )
    claim = LeanClaim(
        id="c1",
        statement="The theorem holds.",
        rationale="A proof establishes the hypothesis.",
        verifier=LeanVerifier(kind=VerifierKind.LEAN),
        designs=[LeanDesign(id="d1", runs=[run])],
    )
    record = ResearchRecord(
        hypotheses=[Hypothesis(id="h1", statement="The theorem holds.", claims=[claim])]
    )
    record.save(str(tmp_path))
    results = tmp_path / ".research" / "results" / "proof"
    results.mkdir(parents=True)
    (results / "lean.json").write_text("{}")
    latex = tmp_path / ".research" / "latex" / "mdpi"
    latex.mkdir(parents=True)
    (latex / "main.tex").write_text(r"\input{claims.tex}")
    (latex / "claims.tex").write_text(render_claims_tex(record, {}))

    result = await verify_paper(str(tmp_path), "mdpi")
    assert result.stage == "results"
    assert not result.ok
    assert any("values.tex" in problem for problem in result.problems)
