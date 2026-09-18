"""The agent lane and the tool lane read the same material.

`get_prompts(step)` returns the authoring prompt of a step. For the one
step with a backend-LLM tool it renders, from the clone, exactly the prompt
the tool would send; the other steps are plain text.
"""

import json
from pathlib import Path

import pytest

from airas.core.research_paths import RECORD_PATH, RESULTS_DIR
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
from airas.mcp.prompt_registry import PROMPT_STEPS, build_prompt
from airas.usecases.analysis.analyze_experiment import (
    analysis_context_of,
    render_analysis_prompt,
)


def _clone(tmp_path: Path) -> str:
    record = ResearchRecord(
        hypotheses=[
            Hypothesis(
                id="h1",
                statement="Aggregate scores hide per-system failure.",
                claims=[
                    SeyvalClaim(
                        verifier=SeyvalVerifier(kind=VerifierKind.SEYVAL),
                        id="c1",
                        statement="Component-wise beats aggregate.",
                        rationale="r",
                        criterion=Criterion(
                            metric="lddt_pli",
                            subject="proposed",
                            reference="baseline",
                            op=">=",
                            margin=0.02,
                        ),
                        prediction=Prediction(low=0.02, high=0.05, basis="pilot"),
                        designs=[
                            SeyvalDesign(
                                id="d1",
                                summary="s",
                                runs=[
                                    SeyvalRun(run_id="proposed"),
                                    SeyvalRun(run_id="baseline"),
                                ],
                            )
                        ],
                    )
                ],
            )
        ]
    )
    (tmp_path / RECORD_PATH).parent.mkdir(parents=True)
    (tmp_path / RECORD_PATH).write_text(record.model_dump_json())
    for run_id, value in (("proposed", 0.70), ("baseline", 0.60)):
        run_dir = tmp_path / RESULTS_DIR / run_id
        run_dir.mkdir(parents=True)
        (run_dir / "metrics.json").write_text(json.dumps({"lddt_pli": value}))
    return str(tmp_path)


@pytest.mark.parametrize(
    "step", [s for s in PROMPT_STEPS if s != "experiment_analysis"]
)
def test_a_plain_step_needs_no_clone(step):
    result = build_prompt(step)

    assert set(result) == {"step", "prompt", "output_json_schema", "flow"}
    assert result["prompt"].strip()


def test_an_unknown_step_names_the_ones_that_exist():
    with pytest.raises(ValueError, match="experiment_analysis"):
        build_prompt("analysis")


def test_the_analysis_step_renders_from_the_clone(tmp_path: Path):
    with pytest.raises(ValueError, match="local_path"):
        build_prompt("experiment_analysis")

    local_path = _clone(tmp_path)
    rendered = build_prompt("experiment_analysis", local_path)

    # The agent lane reads what the tool lane sends.
    assert rendered["prompt"] == render_analysis_prompt(analysis_context_of(local_path))
    assert "proposed.lddt_pli - baseline.lddt_pli >= 0.02" in rendered["prompt"]
    # Observed from metrics.json; the verdict is update_record's to derive.
    assert (
        "Observed difference: 0.1 (outside the predicted interval)"
        in rendered["prompt"]
    )
    assert "Verdict: pending" in rendered["prompt"]


def test_the_hypothesis_prompt_ends_in_preregister_record_shape():
    schema = build_prompt("hypothesis_and_design")["output_json_schema"]

    assert set(schema["properties"]) == {"literature", "hypotheses"}
    assert "Criterion" in schema["$defs"]


def test_the_code_and_paper_prompts_carry_their_contracts():
    code = build_prompt("experiment_code")["prompt"]
    paper = build_prompt("paper_writing")["prompt"]

    assert "SANITY_VALIDATION: PASS" in code and "metrics.json" in code
    assert r"\input{claims.tex}" in paper and r"\airasval" in paper
    assert "After the experiments" in paper
