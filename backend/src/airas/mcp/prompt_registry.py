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
``input_json_schema`` describing the shape of ``inputs`` it accepts, an
``output_json_schema`` describing exactly the data format to produce, and a
``flow`` note on how the output is used next. Steps that loop internally on
the backend (hypothesis refinement, paper refinement) are intentionally
single-shot in host mode: the host produces the artifact once, at its best,
instead of replaying the backend's iteration loop.
"""

import json
from typing import Any, Optional

from jinja2 import Environment
from pydantic import BaseModel

from airas.core.types.experiment_code import ExperimentCode
from airas.core.types.experiment_history import ExperimentHistory
from airas.core.types.experimental_design import (
    ComputeEnvironment,
    ExperimentalDesign,
)
from airas.core.types.experimental_results import ExperimentalResults
from airas.core.types.paper import PaperContent
from airas.core.types.research_history import ResearchHistory
from airas.core.types.research_hypothesis import ResearchHypothesis
from airas.core.types.research_study import ResearchStudy
from airas.resources.datasets.language.prompt_engineering import (
    PROMPT_ENGINEERING_DATASETS,
)
from airas.resources.models.language.hosted_api import (
    HOSTED_API_MODELS as LLM_API_MODELS,
)
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
from airas.usecases.writers.write_subgraph.nodes.generate_note import (
    generate_note,
    map_studies_to_bibtex,
    unmatched_citation_titles,
)
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


# The shape of `inputs` for each step. These both validate the call and are
# published as `input_json_schema`, so a host can see what a step wants
# before calling it rather than discovering it from a validation error.
# Host mode is expected to assemble some of these by hand — a
# research_study_list built from search_papers rows, for instance — and
# there is no other place that shape is written down.


class _ResearchQueriesInputs(BaseModel):
    research_topic: str
    num_queries: int = 2


class _HypothesisInputs(BaseModel):
    research_topic: str
    research_study_list: list[ResearchStudy]


class _ExperimentalDesignInputs(BaseModel):
    research_hypothesis: ResearchHypothesis
    compute_environment: Optional[ComputeEnvironment] = None
    num_models_to_use: int = 2
    num_datasets_to_use: int = 2
    num_comparative_methods: int = 2


class _ExperimentAnalysisInputs(BaseModel):
    research_hypothesis: ResearchHypothesis
    experimental_design: ExperimentalDesign
    experiment_code: ExperimentCode
    experimental_results: ExperimentalResults


class _PaperWritingInputs(BaseModel):
    research_hypothesis: ResearchHypothesis
    experiment_history: ExperimentHistory
    experiment_code: ExperimentCode
    research_study_list: list[ResearchStudy]
    references_bib: str


class _LatexConversionInputs(BaseModel):
    paper_content: PaperContent
    figures_dir: str = "images"


def _render(template: str, data: dict[str, Any]) -> str:
    return Environment().from_string(template).render(data)


def _research_queries(inputs: _ResearchQueriesInputs) -> dict[str, Any]:
    prompt = _render(
        generate_queries_prompt,
        {
            "research_topic": inputs.research_topic,
            "n_queries": inputs.num_queries,
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


def _hypothesis(inputs: _HypothesisInputs) -> dict[str, Any]:
    prompt = _render(
        generate_simple_hypothesis_prompt,
        {
            "research_topic": inputs.research_topic,
            "research_study_list": [
                study.to_formatted_json() for study in inputs.research_study_list
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


def _experimental_design(inputs: _ExperimentalDesignInputs) -> dict[str, Any]:
    prompt = _render(
        generate_experimental_design_prompt,
        {
            "research_hypothesis": inputs.research_hypothesis,
            "compute_environment": inputs.compute_environment or ComputeEnvironment(),
            "model_list": json.dumps(LLM_API_MODELS, indent=4, ensure_ascii=False),
            "dataset_list": json.dumps(
                PROMPT_ENGINEERING_DATASETS, indent=4, ensure_ascii=False
            ),
            "num_models_to_use": inputs.num_models_to_use,
            "num_datasets_to_use": inputs.num_datasets_to_use,
            "num_comparative_methods": inputs.num_comparative_methods,
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


def _experiment_analysis(inputs: _ExperimentAnalysisInputs) -> dict[str, Any]:
    prompt = _render(
        analyze_experiment_prompt,
        {
            "research_hypothesis": inputs.research_hypothesis,
            "experimental_design": inputs.experimental_design,
            "experiment_code": inputs.experiment_code,
            "experimental_results": inputs.experimental_results,
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


def _paper_writing(inputs: _PaperWritingInputs) -> dict[str, Any]:
    # Built once and handed to both readers: the note renders it, and the
    # warning below reports what it could not resolve.
    mapped_studies = map_studies_to_bibtex(
        inputs.research_study_list, inputs.references_bib
    )
    note = generate_note(
        research_hypothesis=inputs.research_hypothesis,
        experiment_history=inputs.experiment_history,
        experiment_code=inputs.experiment_code,
        research_study_list=inputs.research_study_list,
        references_bib=inputs.references_bib,
        mapped_studies=mapped_studies,
    )
    prompt = _render(write_prompt, {"note": note, "tips_dict": section_tips_prompt})
    result: dict[str, Any] = {
        "prompt": prompt,
        "output_json_schema": PaperContent.model_json_schema(),
        "flow": (
            "Author the full paper in one pass, matching output_json_schema. "
            "The result is what you would pass to the latex_conversion step "
            "as paper_content."
        ),
    }
    # The prompt tells the writer not to cite these, and says so nowhere the
    # caller can see. Unattended, that finishes a paper with the citations
    # quietly missing.
    unmatched = unmatched_citation_titles(mapped_studies)
    if unmatched:
        result["warnings"] = [
            f"{len(unmatched)} of {len(inputs.research_study_list)} studies have "
            "no entry in references_bib, so the prompt marks them 'do not cite' "
            "and they will be missing from the paper: "
            + "; ".join(unmatched)
            + ". Titles are matched by title, so pass generate_bibfile's output "
            "verbatim rather than a shortened version."
        ]
    return result


def _latex_conversion(inputs: _LatexConversionInputs) -> dict[str, Any]:
    paper_content = inputs.paper_content
    prompt = _render(
        convert_to_latex_prompt,
        {
            "figures_dir": inputs.figures_dir,
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
            ".research/latex/{template}/main.tex. 3) Write the bibliography "
            "from generate_bibfile to "
            ".research/latex/{template}/references.bib, overwriting the "
            "placeholder the template ships — without this every \\cite "
            "renders as '?'. 4) Check the result with verify_latex before "
            "publishing, then push both files with git."
        ),
    }


_STEP_BUILDERS: dict[str, tuple[type[BaseModel], Any]] = {
    "research_queries": (_ResearchQueriesInputs, _research_queries),
    "hypothesis": (_HypothesisInputs, _hypothesis),
    "experimental_design": (_ExperimentalDesignInputs, _experimental_design),
    "experiment_analysis": (_ExperimentAnalysisInputs, _experiment_analysis),
    "paper_writing": (_PaperWritingInputs, _paper_writing),
    "latex_conversion": (_LatexConversionInputs, _latex_conversion),
}


# Not a generation step, but the same problem: `upload_research_history`
# takes a dict whose accepted shape was written down nowhere, and pydantic's
# default `extra="ignore"` discarded every key that missed it. Publishing it
# here keeps one place to ask "what does this tool want".
_EXTRA_INPUT_SCHEMAS: dict[str, type[BaseModel]] = {
    "research_history": ResearchHistory,
}

_KNOWN_SCHEMAS = (*GENERATION_STEPS, *_EXTRA_INPUT_SCHEMAS)


def get_input_json_schema(step: str) -> dict[str, Any]:
    """The JSON Schema of the `inputs` a step expects."""
    if model := _EXTRA_INPUT_SCHEMAS.get(step):
        return model.model_json_schema()
    if step not in _STEP_BUILDERS:
        # Lists the non-step schemas too, because this is the one place they
        # can be asked for. The generation path below must not: offering
        # research_history as an "available step" would send the caller
        # straight into a second error.
        raise ValueError(
            f"No input schema for '{step}'. Available: {', '.join(_KNOWN_SCHEMAS)}"
        )
    return _STEP_BUILDERS[step][0].model_json_schema()


def _require_known_step(step: str) -> None:
    if step not in _STEP_BUILDERS:
        raise ValueError(
            f"Unknown step '{step}'. Available: {', '.join(GENERATION_STEPS)}"
        )


def build_generation_prompt(step: str, inputs: dict[str, Any]) -> dict[str, Any]:
    _require_known_step(step)
    input_model, builder = _STEP_BUILDERS[step]
    validated = input_model.model_validate(inputs)
    return {
        "step": step,
        "input_json_schema": input_model.model_json_schema(),
        **builder(validated),
    }
