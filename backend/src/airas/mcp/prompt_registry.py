"""Host-authoring prompt registry (dual-mode generation).

Each generation step in AIRAS can run in one of two modes:

- Backend mode: the corresponding MCP tool (e.g. ``generate_paper``) calls
  the backend LLM with AIRAS's curated prompts. Requires an LLM provider
  API key.
- Host mode: the MCP host (Claude Code etc.) authors the artifact itself.
  ``get_generation_prompt`` assembles the *same* prompts from the *same*
  template files the backend nodes use — this module is a thin renderer on
  top of them, so the two modes cannot drift apart.

Every step returns a list of prompt steps plus a ``flow`` description. A
prompt step is either fully rendered (``ready: true``) or a template whose
documented placeholders the host must substitute (e.g. the refine prompt
needs the host's own current draft).
"""

from typing import Any

from jinja2 import Environment

from airas.core.types.experiment_code import ExperimentCode
from airas.core.types.experiment_history import ExperimentHistory
from airas.core.types.experimental_design import ExperimentalDesign
from airas.core.types.experimental_results import ExperimentalResults
from airas.core.types.paper import PaperContent
from airas.core.types.research_hypothesis import ResearchHypothesis
from airas.core.types.research_study import ResearchStudy
from airas.usecases.analyzers.analyze_experiment_subgraph.nodes.analyze_experiment import (
    LLMOutput as AnalyzeExperimentOutput,
)
from airas.usecases.analyzers.analyze_experiment_subgraph.prompts.analyze_experiment_prompt import (
    analyze_experiment_prompt,
)
from airas.usecases.generators.generate_queries_subgraph.nodes.generate_queries import (
    LLMOutput as GenerateQueriesOutput,
)
from airas.usecases.generators.generate_queries_subgraph.prompt.generate_queries_prompt import (
    generate_queries_prompt,
)
from airas.usecases.writers.write_subgraph.nodes.generate_note import generate_note
from airas.usecases.writers.write_subgraph.prompts.refine_prompt import refine_prompt
from airas.usecases.writers.write_subgraph.prompts.section_tips_prompt import (
    section_tips_prompt,
)
from airas.usecases.writers.write_subgraph.prompts.write_prompt import write_prompt

GENERATION_STEPS = ("research_queries", "experiment_analysis", "paper_writing")


def _render(template: str, data: dict[str, Any]) -> str:
    return Environment().from_string(template).render(data)


def _research_queries(inputs: dict[str, Any]) -> dict[str, Any]:
    prompt = _render(
        generate_queries_prompt,
        {
            "research_topic": inputs["research_topic"],
            "n_queries": inputs.get("num_queries", 2),
        },
    )
    return {
        "steps": [
            {
                "name": "generate_queries",
                "ready": True,
                "prompt": prompt,
                "output_json_schema": GenerateQueriesOutput.model_json_schema(),
            }
        ],
        "flow": (
            "Produce output matching output_json_schema; the query_list is "
            "what you would pass to search_papers."
        ),
    }


def _experiment_analysis(inputs: dict[str, Any]) -> dict[str, Any]:
    prompt = _render(
        analyze_experiment_prompt,
        {
            "research_hypothesis": ResearchHypothesis.model_validate(
                inputs["research_hypothesis"]
            ),
            "experimental_design": ExperimentalDesign.model_validate(
                inputs["experimental_design"]
            ),
            "experiment_code": ExperimentCode.model_validate(inputs["experiment_code"]),
            "experimental_results": ExperimentalResults.model_validate(
                inputs["experimental_results"]
            ),
        },
    )
    return {
        "steps": [
            {
                "name": "analyze_experiment",
                "ready": True,
                "prompt": prompt,
                "output_json_schema": AnalyzeExperimentOutput.model_json_schema(),
            }
        ],
        "flow": (
            "Produce output matching output_json_schema; analysis_report is "
            "the analysis text used by the paper-writing step."
        ),
    }


def _paper_writing(inputs: dict[str, Any]) -> dict[str, Any]:
    note = generate_note(
        research_hypothesis=ResearchHypothesis.model_validate(
            inputs["research_hypothesis"]
        ),
        experiment_history=ExperimentHistory.model_validate(
            inputs["experiment_history"]
        ),
        experiment_code=ExperimentCode.model_validate(inputs["experiment_code"]),
        research_study_list=[
            ResearchStudy.model_validate(study)
            for study in inputs["research_study_list"]
        ],
        references_bib=inputs["references_bib"],
    )
    write_message = _render(
        write_prompt, {"note": note, "tips_dict": section_tips_prompt}
    )
    refinement_rounds = inputs.get("writing_refinement_rounds", 2)
    return {
        "steps": [
            {
                "name": "write_paper",
                "ready": True,
                "prompt": write_message,
                "output_json_schema": PaperContent.model_json_schema(),
            },
            {
                "name": "refine_paper",
                "ready": False,
                "placeholders": {
                    "{{ content }}": "your current PaperContent draft as JSON"
                },
                "prompt": refine_prompt,
                "prompt_prefix": (
                    "Prepend the write_paper prompt above, then append this "
                    "refine prompt with the placeholder substituted."
                ),
                "output_json_schema": PaperContent.model_json_schema(),
            },
        ],
        "flow": (
            "1) Author the full paper with the write_paper prompt. "
            f"2) Run the refine_paper step {refinement_rounds} time(s): each "
            "round, substitute {{ content }} with your latest draft and "
            "produce an improved PaperContent. The final draft is what you "
            "would pass to generate_latex as paper_content."
        ),
    }


_STEP_BUILDERS = {
    "research_queries": _research_queries,
    "experiment_analysis": _experiment_analysis,
    "paper_writing": _paper_writing,
}


def build_generation_prompt(step: str, inputs: dict[str, Any]) -> dict[str, Any]:
    if step not in _STEP_BUILDERS:
        raise ValueError(
            f"Unknown step '{step}'. Available: {', '.join(GENERATION_STEPS)}"
        )
    return {"step": step, **_STEP_BUILDERS[step](inputs)}
