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
from airas.core.types.research_hypothesis import (
    HypothesisEvaluation,
    ResearchHypothesis,
)
from airas.core.types.research_study import ResearchStudy
from airas.resources.datasets.prompt_engineering_datasets import (
    PROMPT_ENGINEERING_DATASETS,
)
from airas.resources.models.llm_api_models import LLM_API_MODELS
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
from airas.usecases.generators.generate_hypothesis_subgraph.prompts.evaluate_novelty_and_significance_prompt import (
    evaluate_novelty_and_significance_prompt,
)
from airas.usecases.generators.generate_hypothesis_subgraph.prompts.generate_simple_hypothesis_prompt import (
    generate_simple_hypothesis_prompt,
)
from airas.usecases.generators.generate_hypothesis_subgraph.prompts.refine_hypothesis_prompt import (
    refine_hypothesis_prompt,
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
from airas.usecases.writers.write_subgraph.prompts.refine_prompt import refine_prompt
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


def _hypothesis(inputs: dict[str, Any]) -> dict[str, Any]:
    formatted_studies = [
        ResearchStudy.to_formatted_json(ResearchStudy.model_validate(study))
        for study in inputs["research_study_list"]
    ]
    refinement_rounds = inputs.get("refinement_rounds", 2)
    generate_message = _render(
        generate_simple_hypothesis_prompt,
        {
            "research_topic": inputs["research_topic"],
            "research_study_list": formatted_studies,
        },
    )
    evaluate_message = _render(
        evaluate_novelty_and_significance_prompt,
        {
            "research_topic": inputs["research_topic"],
            "research_study_list": formatted_studies,
            "new_hypothesis": "{{ new_hypothesis }}",
        },
    )
    refine_message = _render(
        refine_hypothesis_prompt,
        {
            "research_topic": inputs["research_topic"],
            "research_study_list": formatted_studies,
            "current_hypothesis": "{{ current_hypothesis }}",
            "novelty_reason": "{{ novelty_reason }}",
            "significance_reason": "{{ significance_reason }}",
            "evaluated_hypothesis_history": "{{ evaluated_hypothesis_history }}",
        },
    )
    return {
        "steps": [
            {
                "name": "generate_hypothesis",
                "ready": True,
                "prompt": generate_message,
                "output_json_schema": ResearchHypothesis.model_json_schema(),
            },
            {
                "name": "evaluate_novelty_and_significance",
                "ready": False,
                "placeholders": {
                    "{{ new_hypothesis }}": "the hypothesis to evaluate, as JSON"
                },
                "prompt": evaluate_message,
                "output_json_schema": HypothesisEvaluation.model_json_schema(),
            },
            {
                "name": "refine_hypothesis",
                "ready": False,
                "placeholders": {
                    "{{ current_hypothesis }}": "the latest hypothesis as JSON",
                    "{{ novelty_reason }}": "novelty_reason from its evaluation",
                    "{{ significance_reason }}": (
                        "significance_reason from its evaluation"
                    ),
                    "{{ evaluated_hypothesis_history }}": (
                        "earlier (hypothesis, evaluation) pairs as JSON, "
                        "oldest first; empty string on the first refinement"
                    ),
                },
                "prompt": refine_message,
                "output_json_schema": ResearchHypothesis.model_json_schema(),
            },
        ],
        "flow": (
            "1) Author a hypothesis with the generate_hypothesis prompt. "
            "2) Evaluate it with evaluate_novelty_and_significance. "
            "3) If novelty_score >= 9 and significance_score >= 9, stop. "
            f"Otherwise refine with refine_hypothesis and re-evaluate, up to "
            f"{refinement_rounds} refinement round(s). The final hypothesis "
            "is what you would pass to the experimental_design step."
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
        "steps": [
            {
                "name": "generate_experimental_design",
                "ready": True,
                "prompt": prompt,
                "output_json_schema": ExperimentalDesignOutput.model_json_schema(),
            }
        ],
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
        "steps": [
            {
                "name": "convert_to_latex",
                "ready": True,
                "prompt": prompt,
                "output_json_schema": PaperContent.model_json_schema(),
            }
        ],
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
