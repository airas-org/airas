"""Capabilities and credentials."""

import os
from typing import Any

from airas.core.credentials import SETUP_INSTRUCTIONS, refresh_environment
from airas.core.types.llm_provider import LLMProvider
from airas.infra.litellm_client import (
    PROVIDER_REQUIRED_ENV_VARS as LITELLM_PROVIDER_REQUIRED_ENV_VARS,
)
from airas.infra.litellm_client import (
    LiteLLMClient,
)
from airas.infra.llm_provider_resolver import (
    RIKYU_BASE_URL_ENV,
    RIKYU_DEFAULT_BASE_URL,
    detect_available_providers,
)
from airas.mcp.app import mcp
from airas.mcp.context import (
    _LITELLM_PROVIDER_NAME,
)
from airas.mcp.prompt_registry import build_generation_prompt, get_input_json_schema


@mcp.tool()
def get_available_llms(include_models: bool = False) -> dict[str, Any]:
    """Report which LLMs are usable with the currently configured API keys.

    Reads credentials fresh (so keys added or rotated since the server
    started are picked up) and, for each known LLM provider, reports whether
    its required API key(s) are present. Call this before the LLM-backed
    tools (`analyze_experiment`, `verify_paper_values` with a model) to know
    which will
    run and which model names you may pass — a tool whose model belongs to an
    unconfigured provider fails fast with the missing key named. This tool
    itself needs no API key.

    Set `include_models` to true to also list, per configured provider, the
    model names in litellm's catalog. It defaults to false because some
    providers return hundreds of models, which bloats the response; request
    it only when you need to choose a specific model.

    Scope: this reports the **LiteLLM** view — provider credentials
    (`LITELLM_PROVIDER_REQUIRED_ENV_VARS`) and litellm's model catalog. Every
    generation tool executes via litellm and accepts any model name litellm
    can route to the configured providers, so a listed provider/model is
    usable by all of them.

    Returns:
    - `any_provider_configured`: whether at least one provider is usable
    - `configured_providers`: sorted provider names that are ready
    - `providers`: per-provider `configured` flag, `required_env_vars`,
      `missing_env_vars`, and (when configured and requested) `models` /
      `model_count`
    - `setup_instructions`: how to add keys, present only when none are set
    """
    refresh_environment()
    available = detect_available_providers(LITELLM_PROVIDER_REQUIRED_ENV_VARS)

    providers: list[dict[str, Any]] = []
    for provider, required in LITELLM_PROVIDER_REQUIRED_ENV_VARS.items():
        configured = provider in available
        entry: dict[str, Any] = {
            "provider": provider.value,
            "configured": configured,
            "required_env_vars": required,
            "missing_env_vars": [name for name in required if not os.getenv(name)],
        }
        if configured and include_models:
            if provider is LLMProvider.RIKYU:
                # litellm's catalog has no entries for this endpoint, so an
                # empty list here would read as "configured but no models".
                # Refuse explicitly and point at the endpoint's own listing.
                base_url = (
                    os.getenv(RIKYU_BASE_URL_ENV, "").strip() or RIKYU_DEFAULT_BASE_URL
                ).rstrip("/")
                entry["models_error"] = (
                    f"litellm's catalog cannot list '{provider.value}' models. "
                    f"Query the endpoint itself — GET {base_url}/models with "
                    "'Authorization: Bearer $RIKYU_API_KEY' — and pass a "
                    f"model as '{provider.value}/<model ID>'."
                )
            else:
                litellm_name = _LITELLM_PROVIDER_NAME.get(provider, provider.value)
                try:
                    models = sorted(
                        LiteLLMClient.get_valid_models(provider=litellm_name)
                    )
                    entry["model_count"] = len(models)
                    entry["models"] = models
                except Exception as exc:  # never let catalog lookup fail the tool
                    entry["models_error"] = str(exc)
        providers.append(entry)

    return {
        "any_provider_configured": bool(available),
        "configured_providers": sorted(p.value for p in available),
        "providers": providers,
        "setup_instructions": None if available else SETUP_INSTRUCTIONS,
    }


@mcp.tool()
def get_generation_prompt(step: str, inputs: dict[str, Any]) -> dict[str, Any]:
    """Assemble AIRAS's curated prompt(s) for a generation step so you (the
    MCP host) can author the artifact yourself — no LLM API key required.

    Generation steps run in one of two modes: the backend-LLM tool
    (`analyze_experiment`,
    needs a provider key) or host mode via this tool. Both use the same
    prompt templates, so quality guidance is identical. Prefer host mode
    when no LLM provider key is configured, or when your own context (the
    conversation, code you wrote) should inform the writing.

    `step` and the required `inputs` keys:
    - "research_queries": research_topic, num_queries (optional)
    - "hypothesis": research_topic, research_study_list
    - "experimental_design": research_hypothesis, compute_environment
      (optional), num_models_to_use / num_datasets_to_use /
      num_comparative_methods (optional)
    - "experiment_analysis": research_hypothesis, experimental_design,
      experiment_code ({"files": {path: content}}), experimental_results
    - "paper_writing": research_hypothesis, experiment_history,
      experiment_code, research_study_list, references_bib
    - "latex_conversion": paper_content, figures_dir (optional)

    Returns a fully rendered `prompt`, an `input_json_schema` describing the
    exact shape of `inputs` for this step, an `output_json_schema` describing
    exactly the data format to produce in one pass, and a `flow` note on
    how the output feeds the next step. Call `get_input_schema` first if you
    are assembling an input by hand — `research_study_list` entries in
    particular are `ResearchStudy` objects, not `search_papers` rows, and
    share no key names with them.
    """
    return build_generation_prompt(step, inputs)


@mcp.tool()
def get_input_schema(step: str) -> dict[str, Any]:
    """The JSON Schema of an input a tool takes.

    Use before assembling one by hand, so the shape is known up front
    instead of being discovered through a validation error — or, worse, not
    discovered at all. `step` is any of `get_generation_prompt`'s steps. No
    API keys required.

    Assembling `research_study_list` from `search_papers` output is the
    common case and needs a translation: a search row's `authors`,
    `citations` and `arxiv_id` live under `meta_data` on a `ResearchStudy`,
    and only `title` is required — a study with just `title` and `abstract`
    is valid, so nothing has to be invented for papers whose full text was
    not retrieved.
    """
    return get_input_json_schema(step)
