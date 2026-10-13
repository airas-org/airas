from pathlib import Path

import pytest

from airas.core.types.latex import LatexBuildReport
from airas.core.types.paper_verification import PaperVerification
from airas.core.types.record_verification import RecordVerification
from airas.core.types.research_record import ResearchRecord
from airas.mcp.tools import publication
from airas.mcp.tools import record as record_tools
from airas.research_record.render.render_claims_tex import render_claims_tex


async def test_record_verification_needs_no_paper(tmp_path: Path) -> None:
    ResearchRecord().save(str(tmp_path))
    result = await record_tools.verify_record(str(tmp_path), check_provenance=False)
    assert result["ok"], result["problems"]
    # no git history here, so the history check itself is the one unverified row
    assert result["declarations"] == {"verified": 0, "mismatch": 0, "unverified": 1}
    assert result["report"] == ".research/verification.md"
    assert (tmp_path / result["report"]).read_text().startswith("# verify-record")


async def test_a_missing_record_is_reported_and_the_report_still_written(
    tmp_path: Path,
) -> None:
    result = await record_tools.verify_record(str(tmp_path), check_provenance=False)
    assert not result["ok"] and "record.json" in result["problems"][0]
    assert (tmp_path / result["report"]).is_file()


async def test_paper_values_are_verified_without_running_the_record_check(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    record = ResearchRecord()
    record.save(str(tmp_path))
    latex = tmp_path / ".research" / "latex" / "mdpi"
    latex.mkdir(parents=True)
    (latex / "main.tex").write_text(r"\input{claims.tex}")
    (latex / "claims.tex").write_text(render_claims_tex(record, {}))
    monkeypatch.setattr(
        publication,
        "verify_record",
        lambda *a, **k: pytest.fail("record has its own check"),
    )
    result = await publication.verify_paper_values(str(tmp_path))
    assert result["ok"], result["problems"]
    assert "record" not in result
    assert "build" not in result


@pytest.mark.parametrize("record_ok", [True, False])
@pytest.mark.parametrize("paper_ok", [True, False])
@pytest.mark.parametrize("build_ok", [True, False])
async def test_pdf_output_requires_record_paper_and_build_to_pass(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    record_ok: bool,
    paper_ok: bool,
    build_ok: bool,
) -> None:
    record = RecordVerification()
    if not record_ok:
        record.append_declaration_status("record.json", "invalid record", "mismatch")
    paper = PaperVerification(
        ok=paper_ok, template="mdpi", problems=[] if paper_ok else ["invalid paper"]
    )
    calls = []

    async def verify_record(*args, **kwargs):
        calls.append("record")
        return record

    async def verify_paper(*args, **kwargs):
        calls.append("paper")
        return paper

    def build(local_path, template, output_path):
        calls.append("build")
        assert bool(output_path) == (record_ok and paper_ok)
        if output_path:
            Path(output_path).write_bytes(b"pdf")
        return LatexBuildReport(ok=build_ok, compiled=True, pdf_path=output_path)

    monkeypatch.setattr(publication, "verify_record", verify_record)
    monkeypatch.setattr(publication, "verify_paper", verify_paper)
    monkeypatch.setattr(publication, "build_paper", build)
    output_path = tmp_path / "paper.pdf"
    result = await publication.verify_latex(
        local_path=str(tmp_path), output_path=str(output_path)
    )

    ok = record_ok and paper_ok and build_ok
    assert calls == ["record", "paper", "build"]
    assert result["ok"] is ok
    assert result["record"]["ok"] is record_ok
    assert result["build"]["ok"] is build_ok
    assert result["pdf"] == (str(output_path) if ok else None)
    assert output_path.is_file() is ok


async def test_verify_latex_builds_without_a_pdf_output_path(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    calls = []

    async def verify_record(*args, **kwargs):
        return RecordVerification()

    async def verify_paper(*args, **kwargs):
        return PaperVerification(ok=True, template="mdpi")

    def build(local_path, template, output_path):
        calls.append((local_path, template, output_path))
        return LatexBuildReport(ok=True, compiled=True)

    monkeypatch.setattr(publication, "verify_record", verify_record)
    monkeypatch.setattr(publication, "verify_paper", verify_paper)
    monkeypatch.setattr(publication, "build_paper", build)
    result = await publication.verify_latex(local_path=str(tmp_path))

    assert calls == [(str(tmp_path), "mdpi", None)]
    assert result["ok"]
    assert result["build"]["compiled"]
    assert result["pdf"] is None
