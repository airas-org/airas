"""step name -> its prompt. The prompt text lives next to the usecase of the
step (usecases/<step>/<step>_prompt.py); a step that also has a backend-LLM
tool (analysis) renders the very prompt the tool sends, from the clone, so
the agent lane and the tool lane read the same material (#1054). The other
steps are plain text: the agent reads the clone itself."""

from typing import Any, Callable

from pydantic import BaseModel, Field

from airas.core.types.research_record import Hypothesis
from airas.usecases.analysis.analyze_experiment import (
    LLMOutput as AnalyzeExperimentOutput,
)
from airas.usecases.analysis.analyze_experiment import (
    analysis_context_of,
    render_analysis_prompt,
)
from airas.usecases.execution.write_experiment_code_prompt import (
    write_experiment_code_prompt,
)
from airas.usecases.hypothesis_and_design.hypothesize_and_design_prompt import (
    hypothesize_and_design_prompt,
)
from airas.usecases.publication.write_paper_prompt import write_paper_prompt


class _Preregistration(BaseModel):
    literature: list[dict[str, Any]] = Field(
        description="preregister_record's `literature`: the papers the hypothesis "
        "rests on, each with its identifiers, fulltext_path and verbatim passages"
    )
    hypotheses: list[Hypothesis]


class _ExperimentCode(BaseModel):
    files: dict[str, str] = Field(description="Relative path -> file content")


class _Paper(BaseModel):
    main_tex: str


def _static(
    prompt: str, output: type[BaseModel], flow: str
) -> Callable[[str | None], dict[str, Any]]:
    def build(local_path: str | None) -> dict[str, Any]:
        return {
            "prompt": prompt,
            "output_json_schema": output.model_json_schema(),
            "flow": flow,
        }

    return build


def _experiment_analysis(local_path: str | None) -> dict[str, Any]:
    if local_path is None:
        raise ValueError("experiment_analysis renders from the clone: pass local_path")
    return {
        "prompt": render_analysis_prompt(analysis_context_of(local_path)),
        "output_json_schema": AnalyzeExperimentOutput.model_json_schema(),
        "flow": (
            "analysis_report is a draft for the Discussion, to be checked against "
            "the numbers. The verdicts come from update_record, not from this text."
        ),
    }


_STEPS: dict[str, Callable[[str | None], dict[str, Any]]] = {
    "hypothesis_and_design": _static(
        hypothesize_and_design_prompt,
        _Preregistration,
        "Pass literature and hypotheses to preregister_record; that call is "
        "the freeze commit.",
    ),
    "experiment_code": _static(
        write_experiment_code_prompt,
        _ExperimentCode,
        "Write the files into the clone, run mode=sanity and make "
        "validate-inputs, then commit and push; run-experiments dispatches.",
    ),
    "experiment_analysis": _experiment_analysis,
    "paper_writing": _static(
        write_paper_prompt,
        _Paper,
        "Save main_tex as .research/latex/{template}/main.tex, run verify_latex "
        "until ok, then commit and push.",
    ),
}
PROMPT_STEPS = tuple(_STEPS)


def build_prompt(step: str, local_path: str | None = None) -> dict[str, Any]:
    if step not in _STEPS:
        raise ValueError(f"Unknown step '{step}'. Available: {', '.join(PROMPT_STEPS)}")
    return {"step": step, **_STEPS[step](local_path)}
