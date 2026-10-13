"""record − coverage: every live declaration is a row of the gate's output,
addressed by id, and what no check compared is listed as skipped."""

import asyncio
import json
from pathlib import Path

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
from airas.research_record.read.declaration_paths import (
    declaration_paths,
    record_json_line,
)
from airas.research_record.render.render_verification_md import (
    render_verification_md,
)
from airas.research_record.verify.verify_record import (
    _append_unchecked_declarations,
    verify_record,
)


def _record() -> ResearchRecord:
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
                summary="same data, same budget",
                runs=[
                    SeyvalRun(run_id="proposed", params={"epochs": 10}),
                    SeyvalRun(run_id="baseline", params={"epochs": 10}),
                ],
            )
        ],
    )
    return ResearchRecord(
        hypotheses=[
            Hypothesis(
                id="h1",
                statement="regularization helps",
                assumptions=["accuracy stands for generalization (c1)"],
                claims=[claim],
            )
        ]
    )


def test_declarations_are_addressed_by_id_and_a_re_append_keeps_its_path() -> None:
    record = _record()
    paths = declaration_paths(record)
    assert (
        paths["hypotheses[h1]/claims[c1]/designs[d1]/runs[proposed]/params/epochs"]
        == 10
    )
    assert paths["hypotheses[h1]/assumptions[0]"].startswith("accuracy")
    assert paths["hypotheses[h1]/claims[c1]/criterion"]["subject"] == "proposed"
    # a revision is an append with the same id: the live entry is the last one
    revised = record.hypotheses[0].claims[0].model_copy(update={"statement": "softer"})
    record.hypotheses[0].claims.append(revised)
    assert declaration_paths(record)["hypotheses[h1]/claims[c1]/statement"] == "softer"


def test_what_no_check_compared_is_listed_as_skipped(tmp_path: Path) -> None:
    _record().save(str(tmp_path))
    result = asyncio.run(
        verify_record(str(tmp_path), check_provenance=False, require_history=False)
    )
    by_path = {s.path: s for s in result.declaration_statuses}
    assert by_path["hypotheses[h1]/claims[c1]/criterion"].status == "verified"
    assert by_path["hypotheses[h1]/claims[c1]/prediction"].status == "unverified"
    assert by_path["hypotheses[h1]/claims[c1]/prediction"].reason == "no check"
    assert (
        by_path["hypotheses[h1]/claims[c1]/designs[d1]/summary"].status == "unverified"
    )
    assert by_path["hypotheses[h1]/assumptions[0]"].status == "unverified"
    # every live declaration appears once at least
    assert set(declaration_paths(_record())) <= set(by_path)


def test_a_compared_parent_covers_its_leaves() -> None:
    verification = RecordVerification()
    verification.append_declaration_status(
        "hypotheses[h1]/claims[c1]/designs[d1]/runs[proposed]/params",
        "manifest",
        "verified",
    )
    _append_unchecked_declarations(_record(), verification)
    unchecked = {
        s.path for s in verification.declaration_statuses if s.status == "unverified"
    }
    assert (
        "hypotheses[h1]/claims[c1]/designs[d1]/runs[proposed]/params/epochs"
        not in unchecked
    )
    assert (
        "hypotheses[h1]/claims[c1]/designs[d1]/runs[baseline]/params/epochs"
        in unchecked
    )


def test_a_declaration_path_resolves_to_its_record_json_line(tmp_path: Path) -> None:
    record = _record()
    revised = record.hypotheses[0].claims[0].model_copy(update={"statement": "softer"})
    record.hypotheses[0].claims.append(revised)
    text = record.save(str(tmp_path)).read_text(encoding="utf-8")
    data = json.loads(text)
    lines = text.splitlines()
    line = record_json_line(data, "hypotheses[h1]/claims[c1]/statement")
    assert line is not None and lines[line - 1].strip() == '"statement": "softer",'
    line = record_json_line(
        data, "hypotheses[h1]/claims[c1]/designs[d1]/runs[baseline]/params/epochs"
    )
    assert line is not None and lines[line - 1].strip() == '"epochs": 10'
    assert record_json_line(data, "hypotheses[h1]/claims[ghost]/statement") is None


def test_the_report_links_each_row_to_the_record_and_its_evidence(
    tmp_path: Path,
) -> None:
    _record().save(str(tmp_path))
    result = asyncio.run(
        verify_record(str(tmp_path), check_provenance=False, require_history=False)
    )
    data = json.loads((tmp_path / ".research/record.json").read_text(encoding="utf-8"))
    markdown = render_verification_md(result, data, "https://github.com/o/r", "abc123")
    assert "## unverified" in markdown
    assert "`hypotheses[h1]/claims[c1]/designs[d1]/summary`" in markdown
    assert "https://github.com/o/r/blob/abc123/.research/record.json#L" in markdown
    assert (
        "[.research/record.json](https://github.com/o/r/blob/abc123/.research/record.json)"
        in markdown
    )
