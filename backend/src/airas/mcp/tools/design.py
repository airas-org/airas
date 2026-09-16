"""Experimental design and resource retrieval."""

from typing import Any

from airas.core.llm_config import uniform_llm_mapping
from airas.core.types.experimental_design import (
    ComputeEnvironment,
    DatasetSubfield,
    ModelSubfield,
)
from airas.core.types.research_hypothesis import ResearchHypothesis
from airas.infra.hugging_face_client import HF_RESOURCE_TYPE
from airas.mcp.app import mcp
from airas.mcp.context import (
    _dump,
    _hugging_face_client,
    _litellm_client,
)
from airas.resources.libraries.library_docs import LIBRARY_DOCS
from airas.usecases.generators.generate_experimental_design_subgraph.generate_experimental_design_subgraph import (
    GenerateExperimentalDesignLLMMapping,
    GenerateExperimentalDesignSubgraph,
)
from airas.usecases.retrieve.retrieve_datasets_subgraph.retrieve_datasets_subgraph import (
    RetrieveDatasetsSubgraph,
)
from airas.usecases.retrieve.retrieve_models_subgraph.retrieve_models_subgraph import (
    RetrieveModelsSubgraph,
)


@mcp.tool()
async def generate_experimental_design(
    research_hypothesis: dict[str, Any],
    model: str,
    compute_environment: dict[str, Any] | None = None,
    num_models_to_use: int = 1,
    num_datasets_to_use: int = 1,
    num_comparative_methods: int = 1,
) -> dict[str, Any]:
    """Design experiments to test a research hypothesis (backend LLM).

    `research_hypothesis` should be the output of `generate_hypothesis`.
    `compute_environment` optionally describes the hardware the experiments
    will run on (e.g. {"gpu_type": "A100", "gpu_count": 1}); it constrains
    the design to what is actually runnable. `model` (required) is the LLM to
    use — call `get_available_llms` to list valid models. Requires an LLM
    provider API key — without one, use
    `get_generation_prompt(step="experimental_design", ...)` and author the
    design yourself.
    """
    env = ComputeEnvironment.model_validate(compute_environment or {})
    result = (
        await GenerateExperimentalDesignSubgraph(
            litellm_client=_litellm_client(),
            compute_environment=env,
            num_models_to_use=num_models_to_use,
            num_datasets_to_use=num_datasets_to_use,
            num_comparative_methods=num_comparative_methods,
            llm_mapping=uniform_llm_mapping(
                GenerateExperimentalDesignLLMMapping, model
            ),
        )
        .build_graph()
        .ainvoke(
            {
                "research_hypothesis": ResearchHypothesis.model_validate(
                    research_hypothesis
                ),
            }
        )
    )
    return _dump(result["experimental_design"])


@mcp.tool()
async def retrieve_models(model_subfield: ModelSubfield) -> dict[str, Any]:
    """List AIRAS's hand-curated candidate models for a subfield.

    Check here first. Subfields follow the shared domain>category taxonomy:
    language ("text_generation", "text_understanding",
    "sequence_to_sequence", "code_generation", "text_embedding",
    "reranking", "hosted_api"), vision ("image_recognition",
    "image_generation"), "vision_language", "speech", "forecasting",
    "protein". Returns a dict
    keyed by model name; each value has model_architecture, task_type,
    huggingface_url, dependent_packages, a runnable code snippet, citation,
    and more. If none of these fit the experimental design, fall back to
    `search_huggingface_hub` (kind="models"), which returns the same shape
    from the live Hub. No API keys required.
    """
    result = (
        await RetrieveModelsSubgraph()
        .build_graph()
        .ainvoke({"model_subfield": model_subfield})
    )
    return result["models_dict"]


@mcp.tool()
async def retrieve_datasets(dataset_subfield: DatasetSubfield) -> dict[str, Any]:
    """List AIRAS's hand-curated candidate datasets for a subfield.

    Check here first. Subfields follow the shared domain>category
    taxonomy: language ("instruction_tuning", "reasoning_evaluation",
    "nlp_tasks", "prompt_engineering", "code_evaluation"),
    "image_recognition", "speech", "vision_language". Returns a dict keyed
    by dataset name; each value has description, task_type, huggingface_url,
    dependent_packages, a runnable code snippet, citation, and more. If none
    fit the experimental design, fall back to `search_huggingface_hub`
    (kind="datasets"), which returns the same shape from the live Hub.
    No API keys required.
    """
    result = (
        await RetrieveDatasetsSubgraph()
        .build_graph()
        .ainvoke({"dataset_subfield": dataset_subfield})
    )
    return result["datasets_dict"]


def _hf_hub_entry(item: dict[str, Any], kind: HF_RESOURCE_TYPE) -> dict[str, Any]:
    """Map one Hugging Face Hub API record to the curated-resource shape."""
    library = item.get("library_name")
    card = item.get("cardData") or {}
    tags = item.get("tags") or []
    if kind == "models":
        task_type = item.get("pipeline_tag")
        packages = [library] if library else []
    else:
        task_type = card.get("task_categories") or card.get("task_ids") or []
        packages = ["datasets"]
    return {
        # curated-compatible core fields (same keys as retrieve_models /
        # retrieve_datasets); code/citation are left empty for Hub results —
        # read the model/dataset card at huggingface_url for usage details.
        "description": item.get("description", ""),
        "model_architecture": "",
        "task_type": task_type,
        "dependent_packages": packages,
        "code": "",
        "citation": "",
        # discovery metadata beyond the curated schema
        "downloads": item.get("downloads"),
        "likes": item.get("likes"),
        "tags": tags,
        "last_modified": item.get("lastModified"),
        "source": "huggingface_hub",
    }


@mcp.tool()
async def search_huggingface_hub(
    kind: HF_RESOURCE_TYPE = "models",
    query: str = "",
    task: str | None = None,
    limit: int = 10,
    sort: str = "downloads",
) -> dict[str, Any]:
    """Live Hugging Face Hub fallback for `retrieve_models`/`retrieve_datasets`.

    Use this only when the curated tools (`retrieve_models` /
    `retrieve_datasets`) have no suitable candidate for the experimental
    design — check them first, then come here to go wider or find newer
    releases. Returns the same shape as the curated tools: a dict keyed by
    resource id, each value carrying the curated-compatible fields
    (description, task_type, huggingface_url, dependent_packages; code and
    citation are empty for Hub results — read the card at huggingface_url),
    plus discovery metadata (downloads, likes, tags, last_modified).

    `kind` is "models" or "datasets"; `query` is free-text search; `task`
    filters by pipeline tag for models (e.g. "text-generation",
    "image-classification", "automatic-speech-recognition") or by tag for
    datasets; `sort` ranks results ("downloads", "likes", "trendingScore",
    "lastModified"). HF_TOKEN is optional (only for gated resources).
    """
    client = _hugging_face_client()
    results = await client.asearch(
        search_type=kind,
        search_query=query,
        limit=limit,
        sort=sort,
        filter=task if kind == "datasets" else None,
        pipeline_tag=task if kind == "models" else None,
        full=True,
    )
    items = results if isinstance(results, list) else results.get("items", results)
    out: dict[str, Any] = {}
    for it in items or []:
        if not isinstance(it, dict):
            continue
        rid = it.get("id") or it.get("modelId")
        if not rid:
            continue
        prefix = "datasets/" if kind == "datasets" else ""
        entry = _hf_hub_entry(it, kind)
        entry["huggingface_url"] = f"https://huggingface.co/{prefix}{rid}"
        out[rid] = entry
    return out


@mcp.tool()
def get_library_docs(
    library: str | None = None,
    domain: str | None = None,
    category: str | None = None,
) -> dict[str, Any]:
    """Look up canonical documentation endpoints for AI research libraries.

    Covers ~165 libraries organized as domain > category (the same shared
    taxonomy as retrieve_models / retrieve_datasets). Domains: foundations,
    language, vision, audio, multimodal, reinforcement_learning,
    time_series, graph, systems, statistics, machine_learning,
    decision_science, interpretability, science. For
    each library returns the official docs URL, the source repository, and
    — where the project publishes one — its `llms.txt` / `llms-full.txt`
    endpoint, which serves the current documentation in a machine-readable
    form. Fetch those endpoints to get up-to-date library guidance while
    writing experiment code. Pass `library` for one entry; `domain` or
    `category` to filter the listing; no arguments to list everything.
    No API keys required.
    """
    if library is not None:
        entry = LIBRARY_DOCS.get(library)
        if entry is None:
            return {
                "error": f"Unknown library: {library!r}.",
                "available": sorted(LIBRARY_DOCS),
            }
        return dict(entry)
    listing = {
        name: {
            "description": e["description"],
            "domain": e["domain"],
            "category": e["category"],
        }
        for name, e in LIBRARY_DOCS.items()
        if (domain is None or e["domain"] == domain)
        and (category is None or e["category"] == category)
    }
    if not listing:
        return {
            "error": f"No libraries match domain={domain!r}, category={category!r}.",
            "available_domains": sorted({e["domain"] for e in LIBRARY_DOCS.values()}),
            "available_categories": sorted(
                {e["category"] for e in LIBRARY_DOCS.values()}
            ),
        }
    return listing
