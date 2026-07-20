"""Host-authoring prompt registry (dual-mode generation).

Each generation step in AIRAS can run in one of two modes:

- Backend mode: the corresponding MCP tool (e.g. ``generate_paper``) calls
  the backend LLM with AIRAS's curated prompts. Requires an LLM provider
  API key.
- Host mode: the MCP host (Claude Code etc.) authors the artifact itself.
  ``get_generation_prompt`` assembles the *same* prompts from the *same*
  template files the backend nodes use — this module is a thin renderer on
  top of them, so the two modes cannot drift apart.

Every step returns a single fully rendered ``prompt``, an
``output_json_schema`` describing exactly the data format to produce, and a
``flow`` note on how the output is used next. Steps that loop internally on
the backend (hypothesis refinement, paper refinement) are intentionally
single-shot in host mode: the host produces the artifact once, at its best,
instead of replaying the backend's iteration loop.
"""

import json
from typing import Any

from jinja2 import Environment

from airas.core.types.experiment_code import ExperimentCode
from airas.core.types.experiment_history import ExperimentHistory
from airas.core.types.experimental_design import (
    ComputeEnvironment,
    ExperimentalDesign,
)
from airas.core.types.experimental_results import ExperimentalResults
from airas.core.types.paper import PaperContent
from airas.core.types.research_hypothesis import ResearchHypothesis
from airas.core.types.research_study import ResearchStudy
from airas.resources.datasets.language.prompt_engineering import (
    PROMPT_ENGINEERING_DATASETS,
)
from airas.resources.models.api.llm import LLM_API_MODELS
from airas.usecases.analyzers.analyze_experiment_subgraph.nodes.analyze_experiment import (
    LLMOutput as AnalyzeExperimentOutput,
)
from airas.usecases.analyzers.analyze_experiment_subgraph.prompts.analyze_experiment_prompt import (
    analyze_experiment_prompt,
)
from airas.usecases.generators.generate_experimental_design_subgraph.nodes.generate_experimental_design import (
    LLMOutput as ExperimentalDesignOutput,
)
from airas.usecases.generators.generate_experimental_design_subgraph.prompts.generate_experimental_design_prompt import (
    generate_experimental_design_prompt,
)
from airas.usecases.generators.generate_hypothesis_subgraph.prompts.generate_simple_hypothesis_prompt import (
    generate_simple_hypothesis_prompt,
)
from airas.usecases.generators.generate_queries_subgraph.nodes.generate_queries import (
    LLMOutput as GenerateQueriesOutput,
)
from airas.usecases.generators.generate_queries_subgraph.prompt.generate_queries_prompt import (
    generate_queries_prompt,
)
from airas.usecases.publication.generate_latex_subgraph.prompts.convert_to_latex_prompt import (
    convert_to_latex_prompt,
)
from airas.usecases.writers.write_subgraph.nodes.generate_note import generate_note
from airas.usecases.writers.write_subgraph.prompts.section_tips_prompt import (
    section_tips_prompt,
)
from airas.usecases.writers.write_subgraph.prompts.write_prompt import write_prompt

GENERATION_STEPS = (
    "research_queries",
    "hypothesis",
    "experimental_design",
    "experiment_analysis",
    "paper_writing",
    "latex_conversion",
)


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
        "prompt": prompt,
        "output_json_schema": GenerateQueriesOutput.model_json_schema(),
        "flow": (
            "Produce output matching output_json_schema; the query_list is "
            "what you would pass to search_papers."
        ),
    }


def _hypothesis(inputs: dict[str, Any]) -> dict[str, Any]:
    prompt = _render(
        generate_simple_hypothesis_prompt,
        {
            "research_topic": inputs["research_topic"],
            "research_study_list": [
                ResearchStudy.to_formatted_json(ResearchStudy.model_validate(study))
                for study in inputs["research_study_list"]
            ],
        },
    )
    return {
        "prompt": prompt,
        "output_json_schema": ResearchHypothesis.model_json_schema(),
        "flow": (
            "Produce a single, novel and significant hypothesis matching "
            "output_json_schema. The result is what you would pass to the "
            "experimental_design step."
        ),
    }


def _experimental_design(inputs: dict[str, Any]) -> dict[str, Any]:
    compute_environment = ComputeEnvironment.model_validate(
        inputs.get("compute_environment") or {}
    )
    prompt = _render(
        generate_experimental_design_prompt,
        {
            "research_hypothesis": ResearchHypothesis.model_validate(
                inputs["research_hypothesis"]
            ),
            "compute_environment": compute_environment,
            "model_list": json.dumps(LLM_API_MODELS, indent=4, ensure_ascii=False),
            "dataset_list": json.dumps(
                PROMPT_ENGINEERING_DATASETS, indent=4, ensure_ascii=False
            ),
            "num_models_to_use": inputs.get("num_models_to_use", 2),
            "num_datasets_to_use": inputs.get("num_datasets_to_use", 2),
            "num_comparative_methods": inputs.get("num_comparative_methods", 2),
        },
    )
    return {
        "prompt": prompt,
        "output_json_schema": ExperimentalDesignOutput.model_json_schema(),
        "flow": (
            "Produce output matching output_json_schema. The result is the "
            "experimental design used to write the experiment code and, "
            "later, by the experiment_analysis and paper_writing steps."
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
        "prompt": prompt,
        "output_json_schema": AnalyzeExperimentOutput.model_json_schema(),
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
    prompt = _render(write_prompt, {"note": note, "tips_dict": section_tips_prompt})
    return {
        "prompt": prompt,
        "output_json_schema": PaperContent.model_json_schema(),
        "flow": (
            "Author the full paper in one pass, matching output_json_schema. "
            "The result is what you would pass to the latex_conversion step "
            "as paper_content."
        ),
    }


def _latex_conversion(inputs: dict[str, Any]) -> dict[str, Any]:
    paper_content = PaperContent.model_validate(inputs["paper_content"])
    prompt = _render(
        convert_to_latex_prompt,
        {
            "figures_dir": inputs.get("figures_dir", "images"),
            "sections": [
                {"name": field, "content": getattr(paper_content, field)}
                for field in PaperContent.model_fields.keys()
                if getattr(paper_content, field)
            ],
        },
    )
    return {
        "prompt": prompt,
        "output_json_schema": PaperContent.model_json_schema(),
        "flow": (
            "1) Produce LaTeX-formatted PaperContent matching "
            "output_json_schema. 2) Embed it into the template yourself: "
            "read .research/latex/{template}/template.tex from your local "
            "clone — it marks insertion points with << title >>, "
            "<< abstract >>, << introduction >>, << related_work >>, "
            "<< background >>, << method >>, << experimental_setup >>, "
            "<< results >>, << conclusion >> — replace each marker with the "
            "corresponding section and save the result as "
            ".research/latex/{template}/main.tex, then push it with git."
        ),
    }


_STEP_BUILDERS = {
    "research_queries": _research_queries,
    "hypothesis": _hypothesis,
    "experimental_design": _experimental_design,
    "experiment_analysis": _experiment_analysis,
    "paper_writing": _paper_writing,
    "latex_conversion": _latex_conversion,
}


def build_generation_prompt(step: str, inputs: dict[str, Any]) -> dict[str, Any]:
    if step not in _STEP_BUILDERS:
        raise ValueError(
            f"Unknown step '{step}'. Available: {', '.join(GENERATION_STEPS)}"
        )
    return {"step": step, **_STEP_BUILDERS[step](inputs)}
