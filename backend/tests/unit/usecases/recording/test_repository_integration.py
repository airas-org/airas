"""A design that runs the method a source's repository holds."""

import pytest
from pydantic import ValidationError

from airas.core.types.research_record import (
    ArgumentValue,
    Criterion,
    Hypothesis,
    LiteratureSource,
    Prediction,
    QuotedPassage,
    Repository,
    RepositoryIntegration,
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

ENTRY = "scigym.controller.Controller.run_benchmark"
MAX_ITERATIONS = "scigym.controller.Controller.__init__.max_iterations"


def _source(method_entry: str = ENTRY, code: bool = True) -> LiteratureSource:
    return LiteratureSource(
        id="s1",
        title="h4duan/SciGym",
        bibkey="h4duan-2025-scigym",
        verified_by="git" if code else "arxiv",
        arxiv_id=None if code else "2507.00001",
        repositories=[
            Repository(
                id="s1.r1",
                url="https://github.com/h4duan/SciGym",
                commit="8" * 40,
                method_entry=method_entry,
            )
        ]
        if code
        else [],
        passages=[
            QuotedPassage(
                id="s1.p1", node_type="setup", quote="max_iterations: int = 5"
            )
        ],
    )


def _record(
    integration: RepositoryIntegration, source: LiteratureSource | None = None
) -> ResearchRecord:
    return ResearchRecord(
        literature=[source or _source()],
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
                                id="d1",
                                repository_integration=integration,
                                runs=[SeyvalRun(run_id="run-1")],
                            )
                        ],
                    )
                ],
            )
        ],
    )


INTEGRATION = RepositoryIntegration(
    repository_id="s1.r1",
    extension_points=["scigym.api.LLM"],
    arguments=[ArgumentValue(argument=MAX_ITERATIONS, value=20)],
)


def test_a_design_running_a_source_with_a_method_entry_passes() -> None:
    assert verify_record_in_itself(_record(INTEGRATION)) == []


@pytest.mark.parametrize("source", [_source(code=False), _source(method_entry="")])
def test_the_source_must_ship_code_with_a_method_entry(
    source: LiteratureSource,
) -> None:
    problems = verify_record_in_itself(_record(INTEGRATION, source))
    assert any("repository_integration.repository_id" in p for p in problems), problems


def test_repository_ids_are_unique_within_a_source() -> None:
    source = _source()
    with pytest.raises(ValidationError, match="unique"):
        LiteratureSource.model_validate(
            {
                **source.model_dump(),
                "repositories": [source.repositories[0].model_dump()] * 2,
            }
        )


def test_an_argument_set_to_none_survives_saving() -> None:
    setting = ArgumentValue(argument=MAX_ITERATIONS, value=None)
    assert "value" in setting.model_dump(exclude_defaults=True)
