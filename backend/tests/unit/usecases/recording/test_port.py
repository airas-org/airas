"""A design's port: an existing method reused from a repository source."""

import pytest
from pydantic import ValidationError

from airas.core.types.research_record import (
    Criterion,
    Hypothesis,
    Knob,
    LiteratureSource,
    Port,
    Prediction,
    QuotedPassage,
    ResearchRecord,
    SeyvalClaim,
    SeyvalDesign,
    SeyvalRun,
    SeyvalVerifier,
    VerifierKind,
)
from airas.research_record.verify._verify_record_in_itself import (
    verify_record_in_itself,
)


def _record(port: Port, source_kind: str = "repository") -> ResearchRecord:
    return ResearchRecord(
        literature=[
            LiteratureSource(
                id="s2",
                kind=source_kind,
                title="h4duan/SciGym",
                bibkey="h4duan-2025-scigym",
                url="https://github.com/h4duan/SciGym",
                commit="8" * 40,
                verified_by="git" if source_kind == "repository" else "doi.org",
                passages=[
                    QuotedPassage(
                        id="s2.p1", node_type="setup", quote="max_iterations: 5"
                    )
                ],
            ),
            LiteratureSource(
                id="s1",
                kind="paper",
                title="SciGym",
                bibkey="scigym-2025",
                arxiv_id="2507.00001",
                verified_by="arxiv",
                passages=[
                    QuotedPassage(id="s1.p1", node_type="setup", quote="5 rounds")
                ],
            ),
        ],
        hypotheses=[
            Hypothesis(
                id="h1",
                statement="h",
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
                                id="d1", port=port, runs=[SeyvalRun(run_id="run-1")]
                            )
                        ],
                    )
                ],
            )
        ],
    )


PORT = Port(
    source="s2",
    entry="scigym.controller.Controller.run_benchmark",
    components=["scigym.controller.Controller.run_benchmark"],
    knobs=[Knob(key="max_iterations", upstream="s2.p1", ours=20)],
)


def test_a_port_that_quotes_its_repository_source_passes() -> None:
    assert verify_record_in_itself(_record(PORT)) == []


def test_the_entry_must_be_a_watched_component() -> None:
    with pytest.raises(ValidationError, match="entry"):
        Port(source="s2", entry="pkg.run", components=["pkg.other"])


def test_the_source_must_be_a_repository() -> None:
    problems = verify_record_in_itself(_record(PORT, source_kind="paper"))
    assert any("not a repository source" in p for p in problems)


@pytest.mark.parametrize("upstream", ["s2.p9", "s1.p1"])
def test_a_knob_must_quote_a_passage_of_the_port_source(upstream: str) -> None:
    port = PORT.model_copy(update={"knobs": [Knob(key="k", upstream=upstream, ours=1)]})
    problems = verify_record_in_itself(_record(port))
    assert any(upstream in p for p in problems)


def test_a_knob_set_to_none_survives_saving() -> None:
    knob = Knob(key="timeout", upstream="s2.p1", ours=None)
    assert "ours" in knob.model_dump(exclude_defaults=True)
