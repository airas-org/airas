"""AIRAS MCP server (stdio).

Exposes AIRAS research subgraphs as MCP tools for use from MCP clients
such as Claude Code and Claude Desktop.

Credentials are read from ~/.airas/credentials.json (see credentials.py):
- LLM providers: OPENAI_API_KEY / ANTHROPIC_API_KEY / GEMINI_API_KEY /
  OPENROUTER_API_KEY / VERCEL_AI_GATEWAY_API_KEY / RIKYU_API_KEY
  (at least one)
- GitHub (repository/experiment tools): GH_PERSONAL_ACCESS_TOKEN

The file is re-read on every tool call, so keys can be added or rotated
without restarting the server.

Run locally:
    uvx --from "airas[mcp]" airas-mcp
"""

import asyncio
import logging
import os
import webbrowser
from io import BytesIO
from pathlib import Path
from typing import Any, Literal
from urllib.parse import urlencode

import httpx
import vl_convert as vlc
from mcp.server.fastmcp import FastMCP
from PIL import Image
from pydantic import BaseModel, ConfigDict, model_validator

from airas.cli import DEFAULT_DASHBOARD_PORT
from airas.core.credentials import SETUP_INSTRUCTIONS, refresh_environment

# LLM mapping classes + helper for building per-node model selection from a
# single externally-supplied model name (no in-code default model exists).
from airas.core.llm_config import uniform_llm_mapping
from airas.core.types.experiment_code import ExperimentCode
from airas.core.types.experiment_history import ExperimentHistory, RunStage
from airas.core.types.experimental_design import (
    ComputeEnvironment,
    DatasetSubfield,
    ExperimentalDesign,
    ModelSubfield,
)
from airas.core.types.experimental_results import ExperimentalResults
from airas.core.types.github import GitHubConfig
from airas.core.types.latex import LATEX_TEMPLATE_NAME
from airas.core.types.llm_provider import LLMProvider
from airas.core.types.paper import PaperContent
from airas.core.types.paper_search import PAPER_SEARCH_SOURCES
from airas.core.types.paper_values import (
    PaperValuesVerificationReport,
    TableSpec,
    ValueDeclaration,
)
from airas.core.types.research_history import ResearchHistory
from airas.core.types.research_hypothesis import ResearchHypothesis
from airas.core.types.research_study import ResearchStudy
from airas.dashboard.launcher import (
    dashboard_url,
    has_bundled_ui,
    is_dashboard_running,
    start_dashboard,
)
from airas.dashboard.launcher import (
    stop_dashboard as stop_dashboard_process,
)
from airas.infra.arxiv_client import ArxivClient
from airas.infra.github_client import GithubClient
from airas.infra.hugging_face_client import HF_RESOURCE_TYPE, HuggingFaceClient
from airas.infra.kroki_client import KrokiClient
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
from airas.infra.openalex_client import OpenAlexClient
from airas.infra.retry_policy import HTTPClientFatalError, HTTPClientRetryableError
from airas.infra.semantic_scholar_client import SemanticScholarClient
from airas.infra.seyval_client import SeyvalClient
from airas.mcp.prompt_registry import build_generation_prompt, get_input_json_schema
from airas.resources.libraries.library_docs import LIBRARY_DOCS
from airas.usecases.analyzers.analyze_experiment_subgraph.analyze_experiment_subgraph import (
    AnalyzeExperimentLLMMapping,
    AnalyzeExperimentSubgraph,
)
from airas.usecases.executors.dispatch_experiment_on_seyval_subgraph.dispatch_experiment_on_seyval_subgraph import (
    DispatchExperimentOnSeyvalSubgraph,
)
from airas.usecases.executors.dispatch_experiment_on_static_runner_subgraph.dispatch_experiment_on_static_runner_subgraph import (
    DispatchExperimentOnStaticRunnerSubgraph,
)
from airas.usecases.executors.dispatch_paper_reproduction_run_subgraph.dispatch_paper_reproduction_run_subgraph import (
    DispatchPaperReproductionRunSubgraph,
)
from airas.usecases.executors.dispatch_parameter_tuning_run_subgraph.dispatch_parameter_tuning_run_subgraph import (
    DispatchParameterTuningRunSubgraph,
)
from airas.usecases.executors.fetch_experiment_results_subgraph.fetch_experiment_results_subgraph import (
    FetchExperimentResultsSubgraph,
)
from airas.usecases.executors.fetch_paper_reproduction_results_subgraph.fetch_paper_reproduction_results_subgraph import (
    FetchPaperReproductionResultsLLMMapping,
    FetchPaperReproductionResultsSubgraph,
)
from airas.usecases.executors.fetch_parameter_tuning_results_subgraph.fetch_parameter_tuning_results_subgraph import (
    FetchParameterTuningResultsSubgraph,
)
from airas.usecases.executors.import_run_outputs_subgraph.import_run_outputs_subgraph import (
    ImportRunOutputsSubgraph,
)
from airas.usecases.generators.dispatch_paper_reproduction_generate_subgraph.dispatch_paper_reproduction_generate_subgraph import (
    DispatchPaperReproductionGenerateLLMMapping,
    DispatchPaperReproductionGenerateSubgraph,
)
from airas.usecases.generators.dispatch_paper_reproduction_generate_subgraph.repro_id import (
    validate_repro_id,
)
from airas.usecases.generators.generate_experimental_design_subgraph.generate_experimental_design_subgraph import (
    GenerateExperimentalDesignLLMMapping,
    GenerateExperimentalDesignSubgraph,
)
from airas.usecases.generators.generate_hypothesis_subgraph.generate_hypothesis_subgraph_v0 import (
    GenerateHypothesisSubgraphV0,
    GenerateHypothesisSubgraphV0LLMMapping,
)
from airas.usecases.generators.generate_queries_subgraph.generate_queries_subgraph import (
    GenerateQueriesLLMMapping,
    GenerateQueriesSubgraph,
)
from airas.usecases.github.download_github_actions_artifacts_subgraph.download_github_actions_artifacts_subgraph import (
    DownloadGithubActionsArtifactsSubgraph,
)
from airas.usecases.github.github_download_subgraph import GithubDownloadSubgraph
from airas.usecases.github.github_upload_subgraph import GithubUploadSubgraph
from airas.usecases.github.prepare_repository_subgraph.prepare_repository_subgraph import (
    PrepareRepositorySubgraph,
)
from airas.usecases.publication.compile_latex_subgraph.compile_latex_subgraph import (
    CompileLatexLLMMapping,
    CompileLatexSubgraph,
)
from airas.usecases.publication.generate_latex_subgraph.generate_latex_subgraph import (
    GenerateLatexLLMMapping,
    GenerateLatexSubgraph,
)
from airas.usecases.publication.nodes.verify_latex_build import verify_latex_build
from airas.usecases.publication.open_in_overleaf_subgraph.nodes.collect_latex_project_files import (
    collect_latex_project_files,
    collect_latex_project_files_local,
)
from airas.usecases.publication.paper_values.charts import (
    CHART_DIR,
    render_chart_bytes,
    substitute_chart_refs,
    write_chart_sidecar,
)
from airas.usecases.publication.paper_values.compute import (
    compute_paper_values as compute_paper_values_node,
)
from airas.usecases.publication.paper_values.compute import load_metrics_data
from airas.usecases.publication.paper_values.latex import (
    VALUES_JSON_FILENAME,
    VALUES_TEX_FILENAME,
    render_values_tex,
)
from airas.usecases.publication.paper_values.tables import (
    TABLES_DIR_NAME,
    TABLES_JSON_FILENAME,
)
from airas.usecases.publication.paper_values.tables import (
    compute_paper_tables as compute_paper_tables_node,
)
from airas.usecases.publication.paper_values.verify import (
    merge_paper_values_report,
    paper_values_configured,
)
from airas.usecases.retrieve.fetch_paper_fulltext_subgraph.fetch_paper_fulltext_subgraph import (
    FetchPaperFulltextSubgraph,
)
from airas.usecases.retrieve.retrieve_datasets_subgraph.retrieve_datasets_subgraph import (
    RetrieveDatasetsSubgraph,
)
from airas.usecases.retrieve.retrieve_models_subgraph.retrieve_models_subgraph import (
    RetrieveModelsSubgraph,
)
from airas.usecases.retrieve.retrieve_paper_subgraph.retrieve_paper_subgraph import (
    RetrievePaperSubgraph,
    RetrievePaperSubgraphLLMMapping,
)
from airas.usecases.retrieve.search_paper_titles_subgraph.nodes.search_paper_titles_from_airas_db import (
    AirasDbPaperSearchIndex,
)
from airas.usecases.retrieve.search_papers_subgraph.search_papers_subgraph import (
    SearchPapersSubgraph,
)
from airas.usecases.verification.paper_verification import paper_values_full_report
from airas.usecases.writers.generate_bibfile_subgraph.generate_bibfile_subgraph import (
    GenerateBibfileSubgraph,
)
from airas.usecases.writers.write_subgraph.write_subgraph import (
    WriteLLMMapping,
    WriteSubgraph,
)

logger = logging.getLogger(__name__)

mcp = FastMCP("airas")

# BM25 index over the AIRAS papers DB; built lazily on first search and
# reused for the lifetime of the server process.
_search_index = AirasDbPaperSearchIndex()

# Process-lifetime HTTP sessions (the stdio server exits with the client,
# so these are closed by process teardown).
_GITHUB_TIMEOUT = httpx.Timeout(connect=10.0, read=60.0, write=120.0, pool=5.0)
_github_sync_session = httpx.Client(follow_redirects=True, timeout=_GITHUB_TIMEOUT)
_github_async_session = httpx.AsyncClient(
    follow_redirects=True, timeout=_GITHUB_TIMEOUT
)
_sync_session = httpx.Client(follow_redirects=True)
_async_session = httpx.AsyncClient(follow_redirects=True)


def _github_client() -> GithubClient:
    refresh_environment()
    token = os.getenv("GH_PERSONAL_ACCESS_TOKEN", "")
    if not token:
        raise RuntimeError(
            f"GH_PERSONAL_ACCESS_TOKEN is not configured. {SETUP_INSTRUCTIONS}"
        )
    return GithubClient(
        github_token=token,
        sync_session=_github_sync_session,
        async_session=_github_async_session,
    )


def _seyval_client() -> SeyvalClient:
    refresh_environment()
    if not os.getenv("SEYVAL_API_KEY"):
        raise RuntimeError(f"SEYVAL_API_KEY is not configured. {SETUP_INSTRUCTIONS}")
    return SeyvalClient(sync_session=_sync_session, async_session=_async_session)


def _kroki_client() -> KrokiClient:
    refresh_environment()
    return KrokiClient(sync_session=_sync_session, async_session=_async_session)


def _arxiv_client() -> ArxivClient:
    return ArxivClient(sync_session=_sync_session, async_session=_async_session)


def _openalex_client() -> OpenAlexClient:
    refresh_environment()  # OPENALEX_API_KEY is optional
    return OpenAlexClient(sync_session=_sync_session, async_session=_async_session)


def _hugging_face_client() -> HuggingFaceClient:
    refresh_environment()  # HF_TOKEN is optional for public resources
    return HuggingFaceClient(sync_session=_sync_session, async_session=_async_session)


def _semantic_scholar_client() -> SemanticScholarClient:
    refresh_environment()  # SEMANTIC_SCHOLAR_API_KEY is optional
    return SemanticScholarClient(
        sync_session=_sync_session, async_session=_async_session
    )


def _litellm_client() -> LiteLLMClient:
    refresh_environment()
    if not detect_available_providers(LITELLM_PROVIDER_REQUIRED_ENV_VARS):
        raise RuntimeError(
            f"No LLM provider API keys are configured. {SETUP_INSTRUCTIONS}"
        )
    return LiteLLMClient()


# airas's LLMProvider enum value -> litellm's ``custom_llm_provider`` name.
# Only GOOGLE and RIKYU diverge (airas "google" vs litellm "gemini"; "rikyu"
# is an airas name for litellm's generic OpenAI-compatible route); every
# other provider's enum value already matches litellm, so we fall back to it.
_LITELLM_PROVIDER_NAME: dict[LLMProvider, str] = {
    LLMProvider.GOOGLE: "gemini",
    LLMProvider.RIKYU: "hosted_vllm",
}


def _dump(value: Any) -> Any:
    return value.model_dump() if isinstance(value, BaseModel) else value


# --- Capabilities / credentials ---


@mcp.tool()
def get_available_llms(include_models: bool = False) -> dict[str, Any]:
    """Report which LLMs are usable with the currently configured API keys.

    Reads credentials fresh (so keys added or rotated since the server
    started are picked up) and, for each known LLM provider, reports whether
    its required API key(s) are present. Call this before the LLM-backed
    tools (`generate_research_queries`, `generate_hypothesis`,
    `generate_experimental_design`, `analyze_experiment`, `generate_paper`,
    `generate_latex`, `compile_latex`, `retrieve_papers`) to know which will
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


# --- Paper discovery & hypothesis ---


@mcp.tool()
def get_generation_prompt(step: str, inputs: dict[str, Any]) -> dict[str, Any]:
    """Assemble AIRAS's curated prompt(s) for a generation step so you (the
    MCP host) can author the artifact yourself — no LLM API key required.

    Generation steps run in one of two modes: the backend-LLM tool
    (`generate_research_queries` / `analyze_experiment` / `generate_paper`,
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
    discovered at all. `step` is any of `get_generation_prompt`'s steps, or
    `research_history` for what `upload_research_history` accepts. No API
    keys required.

    Assembling `research_study_list` from `search_papers` output is the
    common case and needs a translation: a search row's `authors`,
    `citations` and `arxiv_id` live under `meta_data` on a `ResearchStudy`,
    and only `title` is required — a study with just `title` and `abstract`
    is valid, so nothing has to be invented for papers whose full text was
    not retrieved.
    """
    return get_input_json_schema(step)


@mcp.tool()
async def generate_research_queries(
    research_topic: str,
    model: str,
    num_queries: int = 2,
) -> list[str]:
    """Generate academic paper search queries from a research topic (backend LLM).

    Use this first to turn a free-form research topic into effective
    search queries, then pass them to `search_papers`. `model` is required
    (the LLM to use) — call `get_available_llms` to see which models the
    configured keys allow. Requires an LLM provider API key — without one,
    use `get_generation_prompt(step="research_queries", ...)` and author the
    queries yourself.
    """
    result = (
        await GenerateQueriesSubgraph(
            llm_client=_litellm_client(),
            num_paper_search_queries=num_queries,
            llm_mapping=uniform_llm_mapping(GenerateQueriesLLMMapping, model),
        )
        .build_graph()
        .ainvoke({"research_topic": research_topic})
    )
    return result["queries"]


def _parse_paper_sources(sources: str) -> list[str]:
    if not sources.strip() or sources.strip().lower() == "all":
        return list(PAPER_SEARCH_SOURCES)
    selected = [part.strip().lower() for part in sources.split(",") if part.strip()]
    unknown = sorted(set(selected) - set(PAPER_SEARCH_SOURCES))
    if unknown:
        raise ValueError(
            f"Unknown sources: {', '.join(unknown)}. "
            f"Available: {', '.join(PAPER_SEARCH_SOURCES)} (or 'all')."
        )
    return selected


@mcp.tool()
async def search_papers(
    query: str,
    sources: str = "all",
    max_results_per_source: int = 5,
    year: str | None = None,
    search_mode: Literal["keyword", "semantic"] = "keyword",
) -> dict[str, Any]:
    """Search academic papers across multiple sources in parallel.

    Sources: openalex, semantic_scholar, arxiv, airas_db (curated major-ML-
    conference database). Pass a comma-separated subset or "all". `year`
    filters by publication year ("2024" or "2020-2024").

    `search_mode="keyword"` (default) does lexical/relevance search on every
    source. `search_mode="semantic"` does AI-embedding search that matches by
    meaning; it is only supported by `openalex` and requires OPENALEX_API_KEY
    (so pass sources="openalex"). Selecting any other source in semantic mode
    is an error.

    Results are normalized (title, authors, abstract, doi, arxiv_id, pdf_url,
    citations, source) and de-duplicated across sources; failures of
    individual sources are reported in `search_errors` without failing the
    search. Keyword search needs no API keys (SEMANTIC_SCHOLAR_API_KEY /
    OPENALEX_API_KEY optionally raise rate limits). Pass promising titles to
    `retrieve_papers`, or an arxiv_id / doi / pdf_url to
    `fetch_paper_fulltext`.
    """
    refresh_environment()
    selected_sources = _parse_paper_sources(sources)
    if search_mode == "semantic":
        unsupported = sorted(set(selected_sources) - {"openalex"})
        if unsupported:
            raise ValueError(
                f"Semantic search is not supported by: {', '.join(unsupported)}. "
                "Only 'openalex' supports semantic search."
            )
        if not os.getenv("OPENALEX_API_KEY"):
            raise RuntimeError(
                f"Semantic search requires OPENALEX_API_KEY. {SETUP_INSTRUCTIONS}"
            )
    result = (
        await SearchPapersSubgraph(
            openalex_client=_openalex_client(),
            semantic_scholar_client=_semantic_scholar_client(),
            arxiv_client=_arxiv_client(),
            airas_db_search_index=_search_index,
        )
        .build_graph()
        .ainvoke(
            {
                "query": query,
                "sources": selected_sources,
                "max_results_per_source": max_results_per_source,
                "year": year,
                "search_mode": search_mode,
            }
        )
    )
    return {
        "papers": [paper.model_dump(exclude_none=True) for paper in result["papers"]],
        "source_results": result["source_results"],
        "search_errors": result["search_errors"],
    }


@mcp.tool()
async def fetch_paper_fulltext(
    arxiv_id: str | None = None,
    doi: str | None = None,
    pdf_url: str | None = None,
    max_chars: int | None = 40000,
) -> dict[str, Any]:
    """Fetch the full text of a paper by arXiv ID, DOI, or direct PDF URL.

    Identifiers are tried in the order arXiv ID, then PDF URL, then DOI, and
    passing several is useful rather than wasteful: arXiv IDs are fetched
    straight from arXiv, DOIs are resolved to an open-access PDF through
    Semantic Scholar, and a DOI that resolves to nothing falls back to the
    `pdf_url` you supplied. Pass both whenever `search_papers` gave you both
    — a DOI alone returns only the abstract for any paper Semantic Scholar's
    open-access index does not cover, bioRxiv among them.

    Returns the extracted text with `status`: "fulltext", "abstract_only"
    (no open-access PDF found, abstract returned instead), or "not_found".

    A paper can run to 80k+ characters, so the text is capped at `max_chars`
    — **characters, not tokens**, default 40000 — with `total_chars`
    reporting the full length and `truncated` saying whether anything was
    cut. There is no paging: raising the cap re-fetches the paper from the
    start. Neither MCP nor this server imposes a size limit; the cap exists
    because reading a few uncapped papers exhausts a context window, and
    because a client may divert an oversized result to a file. The default
    assumes English prose at roughly four characters per token — lower it
    explicitly for CJK text, where a character is closer to a token.
    No API keys required.
    """
    if not (arxiv_id or doi or pdf_url):
        raise ValueError("One of arxiv_id, doi, or pdf_url must be provided.")
    refresh_environment()
    result = (
        await FetchPaperFulltextSubgraph(
            semantic_scholar_client=_semantic_scholar_client(),
        )
        .build_graph()
        .ainvoke(
            {
                "arxiv_id": arxiv_id,
                "doi": doi,
                "pdf_url": pdf_url,
                "max_chars": max_chars,
            }
        )
    )
    return {
        "text": result["text"],
        "status": result["status"],
        "resolved_from": result["resolved_from"],
        "total_chars": result["total_chars"],
        "truncated": result["truncated"],
    }


@mcp.tool()
async def retrieve_papers(paper_titles: list[str], model: str) -> list[dict[str, Any]]:
    """Retrieve full paper information for the given titles.

    Fetches each paper (via arXiv) and extracts structured research study
    data: abstract, methods, experimental settings, and results. The returned
    objects can be passed to `generate_hypothesis` as `research_study_list`.
    `model` (required) is the LLM to use — call `get_available_llms` to list
    valid models. Requires GH_PERSONAL_ACCESS_TOKEN and an LLM provider API key.
    """
    result = (
        await RetrievePaperSubgraph(
            litellm_client=_litellm_client(),
            arxiv_client=_arxiv_client(),
            github_client=_github_client(),
            llm_mapping=uniform_llm_mapping(RetrievePaperSubgraphLLMMapping, model),
        )
        .build_graph()
        .ainvoke({"paper_titles": paper_titles})
    )
    return [study.model_dump() for study in result["research_study_list"]]


@mcp.tool()
async def generate_hypothesis(
    research_topic: str,
    research_study_list: list[dict[str, Any]],
    model: str,
    refinement_rounds: int = 1,
) -> dict[str, Any]:
    """Generate a novel research hypothesis from a topic and related studies (backend LLM).

    `research_study_list` should be the output of `retrieve_papers`. Higher
    `refinement_rounds` improves quality at the cost of more LLM calls.
    `model` (required) is the LLM to use — call `get_available_llms` to list
    valid models. Requires an LLM provider API key — without one, use
    `get_generation_prompt(step="hypothesis", ...)` and author the
    hypothesis yourself.
    """
    studies = [ResearchStudy.model_validate(study) for study in research_study_list]
    result = (
        await GenerateHypothesisSubgraphV0(
            litellm_client=_litellm_client(),
            refinement_rounds=refinement_rounds,
            llm_mapping=uniform_llm_mapping(
                GenerateHypothesisSubgraphV0LLMMapping, model
            ),
        )
        .build_graph()
        .ainvoke(
            {
                "research_topic": research_topic,
                "research_study_list": studies,
            }
        )
    )
    return result["research_hypothesis"].model_dump()


# --- Experimental design ---


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


# --- Experiment repository & execution (GitHub Actions) ---


@mcp.tool()
async def prepare_repository(
    github_owner: str,
    repository_name: str,
    branch_name: str = "main",
    is_private: bool = True,
) -> dict[str, Any]:
    """Create and initialize a GitHub repository for running experiments.

    Sets up the repository (from the AIRAS experiment template) and the
    working branch. Run this once before `dispatch_code_generation`.
    Returns `html_url` and `clone_url` alongside the readiness flags, so the
    next step — cloning it locally — needs nothing reconstructed by hand.
    Requires GH_PERSONAL_ACCESS_TOKEN.
    """
    config = GitHubConfig(
        github_owner=github_owner,
        repository_name=repository_name,
        branch_name=branch_name,
    )
    result = (
        await PrepareRepositorySubgraph(
            github_client=_github_client(),
            is_github_repo_private=is_private,
        )
        .build_graph()
        .ainvoke({"github_config": config})
    )
    return {
        "is_repository_ready": result["is_repository_ready"],
        "is_branch_ready": result["is_branch_ready"],
        "html_url": result["html_url"],
        "clone_url": result["clone_url"],
    }


@mcp.tool()
async def dispatch_experiment(
    github_owner: str,
    repository_name: str,
    branch_name: str,
    run_id: str,
    run_stage: Literal["sanity", "pilot", "full"] = "sanity",
    runner_label: list[str] | None = None,
    backend: Literal["github_actions", "seyval"] = "github_actions",
    compute_type: str = "gpu-a10",
    compute_id: str | None = None,
    inputs_from_runs: list[str] | None = None,
    time_limit: str | None = None,
    resource_count: int | None = None,
    required_env_vars: list[str] | None = None,
) -> dict[str, Any]:
    """Start an experiment run (asynchronous). The code must already be pushed.

    `run_stage` selects the stage, in increasing scale: "sanity" for a quick
    correctness run, "pilot" for a small preliminary one, "full" for the real
    experiment. `run_id` identifies the experiment run defined by the
    experiment code (one config/run/{run_id}.yaml). Pass the same stage to
    `import_run_outputs` to collect a Seyval run's results afterwards.

    `backend` selects where the run executes:
    - "github_actions" (default): dispatches a workflow in the experiment
      repository. `runner_label` picks the runner. Track progress with
      `get_workflow_runs` and collect outputs with `fetch_experiment_results`.
      Requires GH_PERSONAL_ACCESS_TOKEN.
    - "seyval": executes on the Seyval compute platform (GPU without GitHub
      Actions limits). `compute_id` picks the machine — normally a cluster
      you registered, "byo:<uuid>" from the Seyval MCP server's
      `list_computes`; it defaults to SEYVAL_COMPUTE_ID, and without either the
      run goes to Seyval-managed compute. `compute_type` sets the resource
      request in both cases (e.g. "cpu-general", "gpu-a10"). Seyval keeps the run's
      results on its own side, so call `import_run_outputs` once the run
      finishes — before `fetch_experiment_results`, which reads the
      repository.

    `required_env_vars` lists the env vars Seyval must have registered before
    it will start the run, and defaults to `["WANDB_API_KEY"]`. Seyval
    rejects the run outright when one is missing, so pass `[]` for an
    experiment that does not use Weights & Biases rather than registering a
    dummy key.

    `inputs_from_runs`, `time_limit` and `resource_count` apply to "seyval"
    only. `inputs_from_runs` takes `execution_id`s of earlier completed runs
    and restores their outputs into this run's working directory at the paths
    they were written to, so a run can consume what a previous one produced.
    `time_limit` (e.g. "24:00:00") and `resource_count` request per-run
    resources from a registered cluster; accepted values are in its
    `run_profile` from `list_computes`.

    Track progress and fetch execution errors with
    `get_experiment_run_status`. For "seyval" the returned `execution_id` is
    passed directly; for "github_actions" the workflow-dispatch API returns
    no id, so discover the run id with `get_workflow_runs` first.
    """
    # Both backends record the stage: Seyval in the run's experiment id, GitHub
    # Actions as run_experiment.yml's `mode` input.
    stage = RunStage(run_stage)

    if backend == "seyval":
        # Resolve the client first: it is what loads the stored credentials
        # into the environment that SEYVAL_COMPUTE_ID is read from.
        client = _seyval_client()
        resolved_compute_id = compute_id or os.getenv("SEYVAL_COMPUTE_ID") or None
        seyval_result = (
            await DispatchExperimentOnSeyvalSubgraph(
                seyval_client=client,
                compute_id=resolved_compute_id,
                run_stage=stage,
                compute_type=compute_type,
                inputs_from_runs=inputs_from_runs,
                time_limit=time_limit,
                resource_count=resource_count,
                required_env_vars=required_env_vars,
            )
            .build_graph()
            .ainvoke(
                {
                    "github_config": GitHubConfig(
                        github_owner=github_owner,
                        repository_name=repository_name,
                        branch_name=branch_name,
                    ),
                    "run_id": run_id,
                }
            )
        )
        return {
            "dispatched": seyval_result["dispatched"],
            "backend": "seyval",
            "compute_id": resolved_compute_id,
            "execution_id": seyval_result["seyval_run_id"],
            "execution_url": seyval_result["seyval_run_url"],
        }

    result = (
        await DispatchExperimentOnStaticRunnerSubgraph(
            github_client=_github_client(),
            runner_label=runner_label or ["ubuntu-latest"],
            run_stage=stage,
        )
        .build_graph()
        .ainvoke(
            {
                "github_config": GitHubConfig(
                    github_owner=github_owner,
                    repository_name=repository_name,
                    branch_name=branch_name,
                ),
                "run_id": run_id,
            }
        )
    )
    return {"dispatched": result["dispatched"], "backend": "github_actions"}


@mcp.tool()
async def get_experiment_run_status(
    execution_id: str,
    backend: Literal["github_actions", "seyval"] = "github_actions",
    github_owner: str | None = None,
    repository_name: str | None = None,
    log_tail_lines: int = 200,
) -> dict[str, Any]:
    """Check one experiment run and fetch its execution logs (non-blocking).

    `execution_id` identifies the run on the selected `backend`: the
    `execution_id` returned by `dispatch_experiment(backend="seyval")`, or a
    `workflow_run_id` from `get_workflow_runs` for "github_actions" (pass
    `github_owner` and `repository_name` in that case).

    Returns the run status and, once the run has finished, the last
    `log_tail_lines` lines of stdout and stderr where the backend provides
    them — use stderr to diagnose execution errors and fix the experiment
    code locally.
    """
    if log_tail_lines <= 0:
        raise ValueError("log_tail_lines must be a positive integer")
    log_tail_lines = min(log_tail_lines, 10_000)

    if backend == "github_actions":
        if not github_owner or not repository_name:
            raise ValueError(
                "github_owner and repository_name are required for the "
                "github_actions backend"
            )
        run_info = await _github_client().aget_workflow_run(
            github_owner=github_owner,
            repository_name=repository_name,
            workflow_run_id=int(execution_id),
        )
        if run_info is None:
            raise ValueError(
                f"Workflow run {execution_id} not found in "
                f"{github_owner}/{repository_name}"
            )
        return {
            "execution_id": execution_id,
            "backend": backend,
            "status": run_info.get("status"),
            "conclusion": run_info.get("conclusion"),
            "execution_url": run_info.get("html_url"),
            # Actions job logs are not exposed here; inspect the run page or
            # use download_workflow_artifacts for outputs.
            "stdout_tail": None,
            "stderr_tail": None,
        }

    client = _seyval_client()
    run = await client.aget_run(execution_id)
    status = run.get("status")

    def _tail(text: str) -> str:
        lines = text.splitlines()
        return "\n".join(lines[-log_tail_lines:])

    stdout_tail: str | None = None
    stderr_tail: str | None = None
    if status in ("completed", "failed", "cancelled"):
        try:
            stdout_tail = _tail(await client.aget_run_stdout(execution_id))
        except (HTTPClientFatalError, HTTPClientRetryableError) as exc:
            # logs may not be persisted (yet) for this run
            logger.warning(f"Failed to fetch stdout for run {execution_id}: {exc}")
        try:
            stderr_tail = _tail(await client.aget_run_stderr(execution_id))
        except (HTTPClientFatalError, HTTPClientRetryableError) as exc:
            logger.warning(f"Failed to fetch stderr for run {execution_id}: {exc}")

    return {
        "execution_id": execution_id,
        "backend": backend,
        "status": status,
        "compute_type": run.get("compute_type"),
        "duration_seconds": run.get("duration_seconds"),
        "stdout_tail": stdout_tail,
        "stderr_tail": stderr_tail,
    }


@mcp.tool()
async def get_workflow_runs(
    github_owner: str,
    repository_name: str,
    branch_name: str | None = None,
    limit: int = 5,
) -> list[dict[str, Any]]:
    """Check the status of recent GitHub Actions runs in the experiment repository (non-blocking).

    Returns the most recent dispatched workflow runs with their status and
    conclusion. Use this to track runs started by `dispatch_experiment`
    (backend "github_actions") — poll it between other work instead of
    waiting. Requires GH_PERSONAL_ACCESS_TOKEN.
    """
    response = await _github_client().alist_workflow_runs(
        github_owner=github_owner,
        repository_name=repository_name,
        branch_name=branch_name,
    )
    runs = (response or {}).get("workflow_runs", [])[:limit]
    return [
        {
            "workflow_run_id": run.get("id"),
            "name": run.get("name"),
            "status": run.get("status"),
            "conclusion": run.get("conclusion"),
            "created_at": run.get("created_at"),
            "html_url": run.get("html_url"),
        }
        for run in runs
    ]


@mcp.tool()
async def fetch_experiment_results(
    github_owner: str,
    repository_name: str,
    branch_name: str,
) -> dict[str, Any]:
    """Fetch experiment results from the experiment repository.

    Use after a `dispatch_experiment` run has succeeded. The returned object
    can be passed to `analyze_experiment` as `experimental_results`.
    Requires GH_PERSONAL_ACCESS_TOKEN.
    """
    result = (
        await FetchExperimentResultsSubgraph(github_client=_github_client())
        .build_graph()
        .ainvoke(
            {
                "github_config": GitHubConfig(
                    github_owner=github_owner,
                    repository_name=repository_name,
                    branch_name=branch_name,
                )
            }
        )
    )
    return _dump(result["experimental_results"])


# Stages that re-run the experiment and so write the file names the full run
# owns. A visualization run is additive: it renders figures from an earlier
# run's outputs rather than producing its own metrics.
_PROVISIONAL_RUN_STAGES = frozenset({RunStage.SANITY, RunStage.PILOT})


@mcp.tool()
async def import_run_outputs(
    github_owner: str,
    repository_name: str,
    branch_name: str,
    run_id: str,
    run_stage: Literal["sanity", "pilot", "full", "visualization"] = "full",
    execution_id: str | None = None,
    confirm_overwrite: bool = False,
) -> dict[str, Any]:
    """Copy a Seyval run's result files into the experiment repository.

    Only needed for `backend="seyval"`: Seyval pulls the repository to run it but
    never pushes back, so its results and figures stay in Seyval's storage.
    This commits everything the run wrote under `.research/results/` to
    `branch_name` at the same paths, after which `fetch_experiment_results`,
    `analyze_experiment` and `compile_latex` work as they do for
    "github_actions". A "github_actions" run needs none of this.

    Call it once the run has finished — `get_experiment_run_status` must
    report a terminal status, since outputs are collected at the end.

    `run_id` and `run_stage` identify which run to import, and are the same
    values `dispatch_experiment` was called with.

    A repository path holds one run's results regardless of stage, so
    importing a provisional stage ("sanity" or "pilot") replaces the full
    run's results at the paths they share, and requires
    `confirm_overwrite=True`. "full" is therefore the default, and
    "visualization" needs no confirmation because such a run adds figures
    derived from an earlier run rather than re-running the experiment.

    Pass `execution_id` (the id `dispatch_experiment` returned) to import one
    specific run instead — necessary for older runs, which age out of the
    lookup.

    The same commit records, in `.research/results/.provenance.json`, which
    Seyval run produced each results directory; `verify_paper_values` pins
    its provenance cross-check to that declaration, so results imported any
    other way (or edited afterwards) fail verification. The returned
    `import_commit_sha` identifies the commit holding exactly the imported
    bytes — keep it with the run's records for auditing.

    File contents are downloaded and committed inside airas and are never
    returned. Requires SEYVAL_API_KEY and GH_PERSONAL_ACCESS_TOKEN.
    """
    stage = RunStage(run_stage)
    if stage in _PROVISIONAL_RUN_STAGES and not confirm_overwrite:
        raise ValueError(
            f"A {stage.value} run re-runs the experiment and writes the same "
            f"file names as the full run of '{run_id}', so importing it would "
            "replace the full run's results at those paths. Pass "
            "confirm_overwrite=True to do it anyway."
        )

    result = (
        await ImportRunOutputsSubgraph(
            seyval_client=_seyval_client(),
            github_client=_github_client(),
            run_stage=stage,
            execution_id=execution_id,
        )
        .build_graph()
        .ainvoke(
            {
                "github_config": GitHubConfig(
                    github_owner=github_owner,
                    repository_name=repository_name,
                    branch_name=branch_name,
                ),
                "run_id": run_id,
            }
        )
    )
    return {
        "imported": result["imported"],
        "execution_id": result["execution_id"],
        "imported_paths": result["imported_paths"],
        "total_bytes": result["total_bytes"],
        "import_commit_sha": result["import_commit_sha"],
    }


@mcp.tool()
async def download_workflow_artifacts(
    github_owner: str,
    repository_name: str,
    branch_name: str,
    workflow_run_id: int,
) -> dict[str, Any]:
    """Download the artifacts produced by a GitHub Actions workflow run.

    `workflow_run_id` comes from `get_workflow_runs`. Useful for inspecting
    logs and outputs of a specific run. Requires GH_PERSONAL_ACCESS_TOKEN.
    """
    result = (
        await DownloadGithubActionsArtifactsSubgraph(github_client=_github_client())
        .build_graph()
        .ainvoke(
            {
                "github_config": GitHubConfig(
                    github_owner=github_owner,
                    repository_name=repository_name,
                    branch_name=branch_name,
                ),
                "workflow_run_id": workflow_run_id,
            }
        )
    )
    return _dump(result["artifact_data"])


@mcp.tool()
async def analyze_experiment(
    research_hypothesis: dict[str, Any],
    experimental_design: dict[str, Any],
    experiment_code: dict[str, Any],
    experimental_results: dict[str, Any],
    model: str,
) -> dict[str, Any]:
    """Analyze experiment results against the hypothesis and design.

    Takes the outputs of `generate_hypothesis`, `generate_experimental_design`,
    and `fetch_experiment_results`, and returns a structured analysis
    (findings, whether the hypothesis is supported, and suggested next
    steps). For `experiment_code`, read the code from your local clone and
    pass `{"files": {"<relative path>": "<content>", ...}}`. `model`
    (required) is the LLM to use — call `get_available_llms` to list valid
    models. Requires an LLM provider API key — without one, use
    `get_generation_prompt(step="experiment_analysis", ...)` and write the
    analysis yourself.
    """
    result = (
        await AnalyzeExperimentSubgraph(
            litellm_client=_litellm_client(),
            llm_mapping=uniform_llm_mapping(AnalyzeExperimentLLMMapping, model),
        )
        .build_graph()
        .ainvoke(
            {
                "research_hypothesis": ResearchHypothesis.model_validate(
                    research_hypothesis
                ),
                "experimental_design": ExperimentalDesign.model_validate(
                    experimental_design
                ),
                "experiment_code": ExperimentCode.model_validate(experiment_code),
                "experimental_results": ExperimentalResults.model_validate(
                    experimental_results
                ),
            }
        )
    )
    return _dump(result["experimental_analysis"])


# --- Research history persistence (GitHub) ---


def _reject_unknown_history_keys(research_history: dict[str, Any]) -> None:
    """Refuse a key the model would drop, instead of dropping it.

    ResearchHistory leaves pydantic's default `extra="ignore"` in place, so
    an undeclared top-level key vanishes during validation and the upload
    still reports success. A caller who passed eight keys and had six
    silently discarded learns nothing until a later session restores an
    empty-looking history.

    The strictness belongs here rather than on the model: the same model
    parses `.research/research_history.json` back out of the repository,
    where a file written by hand — which the skills instruct agents to
    do — must not make the whole restore fail.
    """
    if not isinstance(research_history, dict):
        raise ValueError(
            "research_history must be a JSON object keyed by field name, not "
            f"{type(research_history).__name__}."
        )
    unknown = sorted(set(research_history) - set(ResearchHistory.model_fields))
    if not unknown:
        return
    raise ValueError(
        f"research_history has {len(unknown)} key(s) that would be discarded "
        f"without warning: {', '.join(unknown)}. Accepted fields are "
        f"{', '.join(ResearchHistory.model_fields)}. Anything that does not "
        "map onto one of them belongs under `additional_data`, which takes "
        "an arbitrary dict; call get_input_schema('research_history') for "
        "the full shape."
    )


class _ResearchHistoryInput(ResearchHistory):
    """The upload-side view of ResearchHistory: same fields, nothing dropped.

    Typing the tool parameter as this rather than `dict[str, Any]` is what
    puts the field list into the schema the MCP client already reads from
    `tools/list` — a plain dict publishes `additionalProperties: true` and
    no properties at all, which tells the caller nothing. `extra="forbid"`
    both refuses the keys that used to vanish and shows up in that schema,
    so the boundary advertises that it is strict.

    ResearchHistory itself stays lenient: it also parses
    `.research/research_history.json` back out of the repository, where a
    file written by hand — which the skills instruct agents to do — must
    not make the whole restore fail.
    """

    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="before")
    @classmethod
    def _reject_dropped_keys(cls, data: Any) -> Any:
        # pydantic's own "Extra inputs are not permitted" does not mention
        # additional_data, and a caller who is not told about the escape
        # hatch just deletes the data instead of moving it.
        if isinstance(data, dict):
            _reject_unknown_history_keys(data)
        return data


@mcp.tool()
async def upload_research_history(
    github_owner: str,
    repository_name: str,
    branch_name: str,
    research_history: _ResearchHistoryInput,
    commit_message: str | None = None,
) -> dict[str, Any]:
    """Save research history (hypothesis, design, results, ...) to the experiment repository.

    AIRAS persists research state in the GitHub repository, so uploading the
    accumulated history lets you resume work in a later session with
    `download_research_history`. Requires GH_PERSONAL_ACCESS_TOKEN.

    `research_history` takes only the fields in this tool's own schema, and
    any other top-level key is rejected rather than dropped. Anything the
    schema has no home for belongs under `additional_data`, a free-form
    dict. `get_input_schema("research_history")` returns the same shape if
    you would rather ask for it directly.
    """
    result = (
        await GithubUploadSubgraph(_github_client())
        .build_graph()
        .ainvoke(
            {
                "github_config": GitHubConfig(
                    github_owner=github_owner,
                    repository_name=repository_name,
                    branch_name=branch_name,
                ),
                "research_history": research_history,
                "commit_message": commit_message,
            }
        )
    )
    return {"is_github_upload": result["is_github_upload"]}


@mcp.tool()
async def download_research_history(
    github_owner: str,
    repository_name: str,
    branch_name: str,
) -> dict[str, Any]:
    """Load previously saved research history from the experiment repository.

    Restores the state saved by `upload_research_history` so a research
    session can continue where it left off. Requires GH_PERSONAL_ACCESS_TOKEN.
    """
    result = (
        await GithubDownloadSubgraph(_github_client())
        .build_graph()
        .ainvoke(
            {
                "github_config": GitHubConfig(
                    github_owner=github_owner,
                    repository_name=repository_name,
                    branch_name=branch_name,
                )
            }
        )
    )
    return _dump(result["research_history"])


def _resolve_render_output(output_path: str) -> tuple[Path, str]:
    path = Path(output_path).expanduser()
    suffix = path.suffix.lower().lstrip(".")
    if suffix not in ("pdf", "svg", "png"):
        raise ValueError("output_path must end with .pdf, .svg, or .png")
    return path, suffix


def _png_to_pdf(png: bytes) -> bytes:
    buffer = BytesIO()
    with Image.open(BytesIO(png)) as image:
        if image.mode != "RGB":
            # Flatten transparency onto white instead of the black that a
            # plain RGB conversion would produce.
            rgba = image.convert("RGBA")
            rgb = Image.new("RGB", rgba.size, (255, 255, 255))
            rgb.paste(rgba, mask=rgba.getchannel("A"))
        else:
            rgb = image.copy()
    rgb.save(buffer, format="PDF")
    return buffer.getvalue()


@mcp.tool()
async def render_chart(
    vega_lite_spec: dict[str, Any],
    output_path: str,
    local_path: str,
) -> dict[str, Any]:
    """Render a result chart whose data points come from measured metrics.

    Use this for publication-quality result figures. The Vega-Lite spec
    must not contain literal numbers in its data: write every numeric
    datum as `"metric:<run_id>.<path>"` (e.g. `"metric:run_1.accuracy"`),
    and the tool resolves it against `.research/results/` in `local_path`
    itself — so a plotted point cannot be a number no run measured.
    Categorical fields (method names, dataset labels) stay plain strings;
    `calculate`/`expr` transforms are rejected. `\\unverified` has no
    chart equivalent: a number that no run produced does not belong in a
    result figure.

    Save charts as PDF under `.research/results/chart/` in the clone,
    then commit and push — the LaTeX build collects every `*.pdf` under
    `.research/results/`. The unresolved spec is written next to the
    chart as `<file>.chartspec.json`; `verify_paper_values` re-resolves
    and re-renders it and byte-compares, so keep the sidecar committed
    with the chart. `output_path` must end with .pdf, .svg, or .png.
    Rendering runs in-process (vl-convert); no data leaves the machine
    and no API keys are required.
    """
    path, suffix = _resolve_render_output(output_path)

    def _render() -> bytes:
        metrics_data = load_metrics_data(local_path)
        resolved, _ = substitute_chart_refs(vega_lite_spec, metrics_data)
        return render_chart_bytes(resolved, suffix)

    data = await asyncio.to_thread(_render)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)
    sidecar_path = write_chart_sidecar(path, vega_lite_spec, suffix)
    return {
        "output_path": str(path),
        "bytes_written": len(data),
        "chart_spec_path": str(sidecar_path),
        "note": (
            f"commit both files; charts under {CHART_DIR}/ are verified "
            "against a re-render of the sidecar spec"
        ),
    }


@mcp.tool()
async def render_diagram(
    diagram_type: str,
    diagram_source: str,
    output_path: str,
) -> dict[str, Any]:
    """Render a text diagram (diagram-as-code) to a file via Kroki.

    Use this for method/architecture diagrams: write the diagram source in
    a text notation (`diagram_type`: "mermaid", "graphviz", "d2",
    "plantuml", and 20+ more Kroki types). When rendering into a local
    clone of the experiment repository, save the result as a PDF under
    `.research/results/diagram/`, then commit and push — the LaTeX build
    collects every `*.pdf` under `.research/results/`. `output_path` must
    end with .pdf, .svg, or .png; PDF conversion happens locally from the
    SVG (vector). Types whose SVG embeds
    HTML labels (e.g. mermaid) fall back to a raster PDF automatically —
    prefer "graphviz" / "plantuml" when you want vector text. Rendering uses
    the public https://kroki.io by default — set KROKI_BASE_URL to a
    self-hosted instance to keep unpublished diagrams private. No API keys
    required.
    """
    path, suffix = _resolve_render_output(output_path)
    client = _kroki_client()
    if suffix == "pdf":
        svg = await client.arender(diagram_type, diagram_source, "svg")
        if b"<foreignObject" in svg:
            # HTML-in-SVG labels (mermaid etc.) are dropped by the local
            # SVG-to-PDF converter, so rasterize via Kroki's PNG instead.
            png = await client.arender(diagram_type, diagram_source, "png")
            data = await asyncio.to_thread(_png_to_pdf, png)
        else:
            data = await asyncio.to_thread(vlc.svg_to_pdf, svg.decode("utf-8"))
    else:
        data = await client.arender(diagram_type, diagram_source, suffix)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)
    return {"output_path": str(path), "bytes_written": len(data)}


# --- Paper writing & publication ---


@mcp.tool()
async def generate_bibfile(research_study_list: list[dict[str, Any]]) -> str:
    """Generate a BibTeX references file from research studies.

    `research_study_list` should be the output of `retrieve_papers`. Returns
    the .bib content used by `generate_paper` and `generate_latex`.
    No API keys required.
    """
    studies = [ResearchStudy.model_validate(study) for study in research_study_list]
    result = (
        await GenerateBibfileSubgraph()
        .build_graph()
        .ainvoke({"research_study_list": studies})
    )
    return result["references_bib"]


@mcp.tool()
async def generate_paper(
    research_hypothesis: dict[str, Any],
    experiment_history: dict[str, Any],
    experiment_code: dict[str, Any],
    research_study_list: list[dict[str, Any]],
    references_bib: str,
    model: str,
    writing_refinement_rounds: int = 2,
) -> dict[str, Any]:
    """Write the paper content from the completed research (backend LLM).

    Takes the hypothesis, experiment history, experiment code, related
    studies, and the BibTeX file (from `generate_bibfile`), and produces
    structured paper content (title, abstract, sections). Pass the result
    to `generate_latex`. `model` (required) is the LLM to use — call
    `get_available_llms` to list valid models. Requires an LLM provider API
    key — without one, use
    `get_generation_prompt(step="paper_writing", ...)` and author the paper
    yourself in one pass with the same curated prompt.
    """
    result = (
        await WriteSubgraph(
            litellm_client=_litellm_client(),
            paper_content_refinement_iterations=writing_refinement_rounds,
            llm_mapping=uniform_llm_mapping(WriteLLMMapping, model),
        )
        .build_graph()
        .ainvoke(
            {
                "research_hypothesis": ResearchHypothesis.model_validate(
                    research_hypothesis
                ),
                "experiment_history": ExperimentHistory.model_validate(
                    experiment_history
                ),
                "experiment_code": ExperimentCode.model_validate(experiment_code),
                "research_study_list": [
                    ResearchStudy.model_validate(study) for study in research_study_list
                ],
                "references_bib": references_bib,
            }
        )
    )
    return _dump(result["paper_content"])


@mcp.tool()
async def generate_latex(
    paper_content: dict[str, Any],
    references_bib: str,
    model: str,
    latex_template_name: LATEX_TEMPLATE_NAME = "mdpi",
) -> str:
    """Convert paper content into a full LaTeX document (backend LLM).

    `paper_content` should be the output of `generate_paper`. Available
    templates: "mdpi", "iclr2024", "agents4science_2025". Write the returned
    LaTeX to `.research/latex/{template}/main.tex` in your local clone of
    the experiment repository and push it with git, then build the PDF with
    `compile_latex` and/or hand it over with `open_in_overleaf`. `model`
    (required) is the LLM to use — call `get_available_llms` to list valid
    models. Requires an LLM provider API key and GH_PERSONAL_ACCESS_TOKEN —
    without them, use `get_generation_prompt(step="latex_conversion", ...)`
    and do the conversion yourself with the template from your local clone.
    """
    result = (
        await GenerateLatexSubgraph(
            litellm_client=_litellm_client(),
            github_client=_github_client(),
            latex_template_name=latex_template_name,
            llm_mapping=uniform_llm_mapping(GenerateLatexLLMMapping, model),
        )
        .build_graph()
        .ainvoke(
            {
                "paper_content": PaperContent.model_validate(paper_content),
                "references_bib": references_bib,
            }
        )
    )
    return result["latex_text"]


@mcp.tool()
async def compile_latex(
    github_owner: str,
    repository_name: str,
    branch_name: str,
    model: str,
    latex_template_name: LATEX_TEMPLATE_NAME = "mdpi",
    github_actions_agent: Literal["claude_code", "open_code"] = "claude_code",
) -> dict[str, Any]:
    """Build the paper PDF on GitHub Actions (asynchronous).

    One of the two publication exits after main.tex has been pushed to
    `.research/latex/{template}/` (the other is `open_in_overleaf`; they
    are independent and can both be used).
    Dispatches the LaTeX compilation workflow for the pushed sources.
    The workflow materializes every PDF under `.research/results/` and
    `.research/diagrams/` into the template's `images/` with the directory
    structure preserved, so figures need only be pushed, not pre-staged.
    Returns as soon as the dispatch is accepted, which is not a
    compile result — `paper_url` is where the PDF will land if the run
    succeeds, so track the run with `get_workflow_runs`, and use
    `verify_latex` to find out whether the document is actually sound.
    `model` (required) is forwarded to the compilation workflow as the
    coding-agent model (`model_name`) — call `get_available_llms` to list
    valid models. Requires GH_PERSONAL_ACCESS_TOKEN.
    """
    result = (
        await CompileLatexSubgraph(
            github_client=_github_client(),
            latex_template_name=latex_template_name,
            github_actions_agent=github_actions_agent,
            llm_mapping=uniform_llm_mapping(CompileLatexLLMMapping, model),
        )
        .build_graph()
        .ainvoke(
            {
                "github_config": GitHubConfig(
                    github_owner=github_owner,
                    repository_name=repository_name,
                    branch_name=branch_name,
                )
            }
        )
    )
    return {
        "compile_latex_dispatched": result["compile_latex_dispatched"],
        "paper_url": result["paper_url"],
    }


@mcp.tool()
async def verify_latex(
    github_owner: str = "",
    repository_name: str = "",
    branch_name: str = "",
    latex_template_name: LATEX_TEMPLATE_NAME = "mdpi",
    local_path: str | None = None,
    output_path: str | None = None,
    check_provenance: bool = True,
) -> dict[str, Any]:
    """Compile the paper locally and report whether it is actually sound.

    Use this before `open_in_overleaf` or `compile_latex` — those produce a
    link and a dispatch receipt, neither of which tells you the document
    built. This one builds it and answers the questions that decide whether
    the paper is publishable: did a PDF come out (`compiled`, `page_count`),
    do any citations render as `?` (`undefined_citations` — the usual cause
    is writing main.tex without also writing the generated bibliography to
    `.research/latex/{template}/references.bib`, whose shipped version is a
    single placeholder entry), do any `\\ref`s render as `??`
    (`undefined_references`), and is any figure referenced but absent
    (`missing_figures`). `ok` is true only when all of those are clean and
    `errors` — the `!` lines from the log, which is where a missing package
    or a broken environment shows up — is empty too.

    It compiles exactly the file set `open_in_overleaf` would export, so
    what is checked is what would be shipped. The toolchain is still the
    local one — Overleaf builds its own TeX Live image through latexmk — so
    read the two verdicts differently: `ok=False` is a property of the
    document and will follow it anywhere, while `ok=True` says this machine
    built it, not that Overleaf will. A package installed there but not
    here is the likely way the two disagree.

    Pass `local_path` — the absolute path of your local clone — to check the
    working tree with no push and no API keys. Otherwise pass
    `github_owner`/`repository_name`/`branch_name` to check what was pushed
    (requires GH_PERSONAL_ACCESS_TOKEN).

    Pass `output_path` to keep the PDF this build produced — the build
    directory is temporary otherwise, and `pdf_path` in the result says
    where it landed. For a Japanese paper that is the only way to get a PDF
    at all: `compile_latex` runs pdflatex on GitHub Actions, which cannot
    typeset CJK.

    Requires a local TeX distribution. A Japanese document is built with
    lualatex (`texlive-luatex`, `texlive-lang-japanese`); everything else
    with pdflatex.

    When checking a local clone of a paper that uses the value-integrity
    system (a `values.json` written by `compute_paper_values` exists), the
    numbers are verified too: every stated value is recomputed from the
    run outputs, `values.tex` is diffed against a regeneration, every
    `\\airasval` key must be defined, and (unless `check_provenance=False`)
    the local metrics files are cross-checked against the execution
    platform's stored run outputs (currently Seyval) — each referenced
    results directory must be byte-identical to what a completed run of a
    commit in this repository's history actually produced. The full
    report lands under `paper_values` (`paper_values_configured` says
    whether the system is in use; its `provenance.status` is
    "unavailable" when the platform could not be consulted, which does
    not fail the build but is surfaced). On failure `ok` is false and no
    PDF is written to `output_path` — so a PDF this tool hands out states
    verified, provenance-backed numbers.
    """
    refresh_environment()

    paper_values_report = None
    if local_path:
        paper_values_report = await _paper_values_full_report(
            local_path, latex_template_name, check_provenance
        )
        if paper_values_configured(paper_values_report) and not paper_values_report.ok:
            # A PDF handed out by this tool must imply verified numbers.
            output_path = None
        latex_files = await asyncio.to_thread(
            collect_latex_project_files_local, local_path, latex_template_name
        )
    else:
        if not (github_owner and repository_name and branch_name):
            raise ValueError(
                "Provide local_path, or all of github_owner, repository_name "
                "and branch_name."
            )
        latex_files = await asyncio.to_thread(
            collect_latex_project_files,
            GitHubConfig(
                github_owner=github_owner,
                repository_name=repository_name,
                branch_name=branch_name,
            ),
            latex_template_name,
            _github_client(),
        )

    report = await asyncio.to_thread(
        verify_latex_build, latex_files, "main.tex", output_path
    )
    result: dict[str, Any] = report.model_dump()
    if paper_values_report is not None:
        result = merge_paper_values_report(result, paper_values_report)
    return result


async def _paper_values_full_report(
    local_path: str,
    latex_template_name: LATEX_TEMPLATE_NAME,
    check_provenance: bool,
) -> PaperValuesVerificationReport:
    """The shared verification composition, with this server's Seyval client.

    `airas verify-paper` (the CI gate) runs the same composition, so a
    paper judged here and a paper judged in CI are judged identically.
    """
    return await paper_values_full_report(
        local_path, latex_template_name, check_provenance, _seyval_client
    )


@mcp.tool()
async def compute_paper_values(
    local_path: str,
    declarations: list[dict[str, Any]],
    latex_template_name: LATEX_TEMPLATE_NAME = "mdpi",
) -> dict[str, Any]:
    """Turn declared metric expressions into the paper's numbers, deterministically.

    This is the only sanctioned way experimental numbers enter the paper.
    Declare *which* metrics you need and *how* they combine; the tool reads
    the actual run outputs (`.research/results/<run_id>/metrics.json` and
    `comparison/aggregated_metrics.json` in the local clone) and computes
    every value itself. Numbers cannot be passed in, so a value that was
    never measured cannot become a macro.

    Each declaration is `{"key", "op", "refs", "round"}`: `key` names the
    value (`^[a-z][a-z0-9_]*$`); `op` is one of `value` (the single ref
    as-is), `mean` / `std` (over all refs), `diff` (refs[0] - refs[1]), or
    `pct_improve` ((refs[0] - refs[1]) / |refs[1]| * 100); `refs` are
    `"run_id.path.to.metric"` into that run's metrics.json; `round` is the
    optional number of decimal places for display.

    Writes `values.json` (the audit record) and `values.tex` (the macro
    table) into `.research/latex/{template}/`. Then `\\input{values.tex}`
    in main.tex's preamble and write every experimental number as
    `\\airasval{key}` — never as a literal. A legitimate number that no
    declaration can produce (e.g. a value quoted from a cited paper) must
    be wrapped as `\\unverified{...}` so it is surfaced for review. Before
    publishing, run `verify_paper_values`: it recomputes everything from
    the run outputs and fails on any drift, including manual edits to the
    generated files.
    """
    parsed = [ValueDeclaration.model_validate(d) for d in declarations]

    def _run() -> dict[str, Any]:
        metrics_data = load_metrics_data(local_path)
        paper_values = compute_paper_values_node(parsed, metrics_data)
        latex_dir = (
            Path(local_path).expanduser().resolve()
            / ".research"
            / "latex"
            / latex_template_name
        )
        latex_dir.mkdir(parents=True, exist_ok=True)
        values_json_path = latex_dir / VALUES_JSON_FILENAME
        values_tex_path = latex_dir / VALUES_TEX_FILENAME
        values_json_path.write_text(
            paper_values.model_dump_json(indent=2) + "\n", encoding="utf-8"
        )
        values_tex_path.write_text(render_values_tex(paper_values), encoding="utf-8")
        return {
            "values": {v.key: v.display for v in paper_values.values},
            "values_json_path": str(values_json_path),
            "values_tex_path": str(values_tex_path),
            "usage": (
                "\\input{values.tex} in the preamble, then \\airasval{<key>} "
                "wherever the paper states the number"
            ),
        }

    return await asyncio.to_thread(_run)


@mcp.tool()
async def compute_paper_tables(
    local_path: str,
    tables: list[dict[str, Any]],
    latex_template_name: LATEX_TEMPLATE_NAME = "mdpi",
) -> dict[str, Any]:
    """Render the paper's results tables deterministically from run outputs.

    This is the only sanctioned way a results table enters the paper —
    never write a tabular of experimental numbers by hand. Declare the
    layout; the tool reads the metrics itself and renders
    `tables/<key>.tex`, so the cell at (row, column) is always
    `<row.run_id>.<column.ref_path>` and a method's label cannot be
    paired with another run's number.

    Each table is `{"key", "caption", "label"?, "columns", "rows"}`:
    `columns` are `{"header", "ref_path", "round"?}` (ref_path is the
    metric path inside each row's metrics.json, e.g. "accuracy" or
    "loss.final"); `rows` are `{"run_id", "label"}` (run_id is the
    results directory, label the text the paper shows, e.g. "Ours").

    Writes `tables.json` (the audit record) and `tables/<key>.tex` into
    `.research/latex/{template}/`. Then `\\input{tables/<key>.tex}` where
    the table belongs. `verify_paper_values` regenerates every declared
    table and fails on any difference — and on any `tables/*.tex` that
    tables.json does not declare.
    """
    specs = [TableSpec.model_validate(t) for t in tables]

    def _run() -> dict[str, Any]:
        metrics_data = load_metrics_data(local_path)
        paper_tables, rendered = compute_paper_tables_node(specs, metrics_data)
        latex_dir = (
            Path(local_path).expanduser().resolve()
            / ".research"
            / "latex"
            / latex_template_name
        )
        tables_dir = latex_dir / TABLES_DIR_NAME
        tables_dir.mkdir(parents=True, exist_ok=True)
        tables_json_path = latex_dir / TABLES_JSON_FILENAME
        tables_json_path.write_text(
            paper_tables.model_dump_json(indent=2) + "\n", encoding="utf-8"
        )
        written: dict[str, str] = {}
        for key, tex in rendered.items():
            table_path = tables_dir / f"{key}.tex"
            table_path.write_text(tex, encoding="utf-8")
            written[key] = str(table_path)
        return {
            "tables": written,
            "tables_json_path": str(tables_json_path),
            "usage": ("\\input{tables/<key>.tex} where each table belongs in main.tex"),
        }

    return await asyncio.to_thread(_run)


@mcp.tool()
async def verify_paper_values(
    local_path: str,
    latex_template_name: LATEX_TEMPLATE_NAME = "mdpi",
    check_provenance: bool = True,
) -> dict[str, Any]:
    """Check that every number the paper states is the number that was measured.

    The deterministic checks that decide `ok`: every value in
    `values.json` is recomputed from the run outputs under
    `.research/results/` (a tampered record surfaces as a mismatch),
    `values.tex` is regenerated and diffed byte-for-byte (a manual edit
    to the macro table surfaces), every `\\airasval` key main.tex
    references must be defined, every table under `tables/` must match a
    regeneration from `tables.json` (undeclared table files fail), and
    every chart under `.research/results/chart/` must match a re-render
    of its `.chartspec.json` sidecar (a chart without a sidecar fails).
    Unless `check_provenance=False`, the local metrics files are also
    cross-checked against the execution platform's stored run outputs
    (currently Seyval): each referenced results directory must be
    byte-identical to what the run *declared* for it in
    `.research/results/.provenance.json` (written by `import_run_outputs`)
    actually produced, that run must be completed, and its commit must be
    an ancestor of the local HEAD — so a rewritten local metrics.json
    fails even though the recomputation is self-consistent, and quietly
    swapping to a different run of the same experiment surfaces as a
    mismatch. Each check lists the other completed runs of the same
    commit (`sibling_run_ids`); review them — repeated executions mean
    the reported run was a choice. `provenance.status` "unavailable" (no
    credentials, unregistered repository, network) is surfaced without
    failing the local checks.

    `unverified` lists every `\\unverified{...}` the author marked —
    review input, not a failure. Run this after any step that may edit
    main.tex (including compile agents), and treat the list as mandatory
    review items before publishing.
    """
    refresh_environment()
    report = await _paper_values_full_report(
        local_path, latex_template_name, check_provenance
    )
    return report.model_dump()


@mcp.tool()
def open_in_overleaf(
    github_owner: str,
    repository_name: str,
    branch_name: str,
    latex_template_name: LATEX_TEMPLATE_NAME = "mdpi",
    local_path: str | None = None,
) -> dict[str, Any]:
    """Create a link that opens the paper in Overleaf for editing.

    One of the two publication exits for the paper (the other is
    `compile_latex`; they are independent and can both be used).
    Returns `overleaf_url`, which must be shown to the user as a clickable
    link. Opening it in a browser packages the LaTeX project (main.tex,
    bibliography, template assets, plus every figure PDF under
    `.research/results/` and `.research/diagrams/` mapped into `images/`)
    and submits it to Overleaf, creating a new project in the user's
    Overleaf account (login required; each click creates a new project).

    By default the project is read from the experiment repository on GitHub
    (main.tex must have been pushed; requires GH_PERSONAL_ACCESS_TOKEN,
    private repositories work). Pass `local_path` — the absolute path of your local
    clone — to read the working tree on disk instead: no push needed, and
    locally rendered figures are included as-is. Starts the local dashboard
    API in the background if needed.
    """
    refresh_environment()

    port = DEFAULT_DASHBOARD_PORT
    dashboard_status = "already_running"
    if not is_dashboard_running(port):
        start_dashboard(port)
        dashboard_status = "started"

    query: dict[str, str] = {
        "github_owner": github_owner,
        "repository_name": repository_name,
        "branch_name": branch_name,
        "latex_template_name": latex_template_name,
    }
    if local_path:
        query["local_path"] = local_path
    params = urlencode(query)
    overleaf_url = f"{dashboard_url(port)}/airas/v1/latex/overleaf?{params}"
    return {
        "overleaf_url": overleaf_url,
        "dashboard_status": dashboard_status,
        "note": (
            "Show this URL to the user as a clickable link. Opening it in a "
            "browser sends the paper's LaTeX sources to Overleaf and creates "
            "a new editable project there."
        ),
    }


@mcp.tool()
def open_dashboard(
    port: int = DEFAULT_DASHBOARD_PORT, open_browser: bool = True
) -> dict[str, Any]:
    """Launch the AIRAS web dashboard on localhost and return its URL.

    Starts the dashboard server (API + web UI) as a background process,
    or reuses one that is already running on the port. By default the URL
    is also opened in the user's browser. The dashboard keeps running
    after the MCP session ends; stop it with `stop_dashboard`.
    No API keys required to launch.
    """
    # The dashboard process inherits credentials from ~/.airas/credentials.json
    # via the environment, so its API endpoints can call LLM/GitHub APIs.
    refresh_environment()

    url = dashboard_url(port)
    if is_dashboard_running(port):
        status = "already_running"
    else:
        start_dashboard(port)
        status = "started"

    if open_browser:
        webbrowser.open(url)

    result: dict[str, Any] = {"status": status, "url": url}
    if not has_bundled_ui():
        result["warning"] = (
            "This installation has no bundled web UI (development checkout?), "
            "so only the API is served. Install the published package "
            "(`uvx airas`) for the full dashboard."
        )
    return result


@mcp.tool()
def stop_dashboard() -> dict[str, Any]:
    """Stop the AIRAS web dashboard started by `open_dashboard`."""
    return stop_dashboard_process()


# --- Paper reproduction ---


@mcp.tool()
async def dispatch_paper_reproduction_generate(
    github_owner: str,
    repository_name: str,
    branch_name: str,
    paper_url: str,
    instruction: str,
    model: str,
    repo_url: str = "",
    github_actions_agent: Literal["claude_code", "open_code"] = "claude_code",
    runner_label: list[str] | None = None,
) -> dict[str, Any]:
    """Start paper-reproduction code generation on GitHub Actions (asynchronous).

    Dispatches a workflow that reads `paper_url`, picks a figure or table to
    reproduce (guided by `instruction`), and generates the code. Returns
    immediately with `dispatched`; track progress with `get_workflow_runs` and
    run the experiment with `dispatch_paper_reproduction_run` once the run
    succeeds. `model` (required) is forwarded to the workflow as the coding-
    agent model (`model_name`) — call `get_available_llms` to list valid
    models. Requires GH_PERSONAL_ACCESS_TOKEN.

    Returns repro_id, which identifies this reproduction's directory
    (.reproduction/<repro_id>/) and must be passed to every subsequent
    reproduction tool.
    """
    result = (
        await DispatchPaperReproductionGenerateSubgraph(
            github_client=_github_client(),
            runner_label=runner_label,
            llm_mapping=uniform_llm_mapping(
                DispatchPaperReproductionGenerateLLMMapping, model
            ),
        )
        .build_graph()
        .ainvoke(
            {
                "github_config": GitHubConfig(
                    github_owner=github_owner,
                    repository_name=repository_name,
                    branch_name=branch_name,
                ),
                "paper_url": paper_url,
                "instruction": instruction,
                "repo_url": repo_url,
                "github_actions_agent": github_actions_agent,
            }
        )
    )
    return {"dispatched": result["dispatched"], "repro_id": result["repro_id"]}


@mcp.tool()
async def dispatch_paper_reproduction_run(
    github_owner: str,
    repository_name: str,
    branch_name: str,
    repro_id: str,
    repo_url: str = "",
    runner_label: list[str] | None = None,
) -> dict[str, Any]:
    """Start a paper-reproduction run on GitHub Actions (asynchronous).

    Use after a `dispatch_paper_reproduction_generate` run has succeeded.
    `repro_id` is the ID returned by `dispatch_paper_reproduction_generate`.
    Returns immediately with `dispatched`; track progress with
    `get_workflow_runs` and collect outputs with
    `fetch_paper_reproduction_results`. Requires GH_PERSONAL_ACCESS_TOKEN.
    """
    validate_repro_id(repro_id)
    result = (
        await DispatchPaperReproductionRunSubgraph(
            github_client=_github_client(),
            runner_label=runner_label,
        )
        .build_graph()
        .ainvoke(
            {
                "github_config": GitHubConfig(
                    github_owner=github_owner,
                    repository_name=repository_name,
                    branch_name=branch_name,
                ),
                "repro_id": repro_id,
                "repo_url": repo_url,
            }
        )
    )
    return {"dispatched": result["dispatched"]}


@mcp.tool()
async def fetch_paper_reproduction_results(
    github_owner: str,
    repository_name: str,
    branch_name: str,
    repro_id: str,
    model: str,
) -> dict[str, Any]:
    """Fetch and validate the results of a paper reproduction run.

    Use after a `dispatch_paper_reproduction_run` has succeeded. `repro_id` is
    the ID returned by `dispatch_paper_reproduction_generate`. Returns the
    self-reported result, a validation verdict, and the reproduced
    figure/table. `model` (required) is the LLM used to judge the
    reproduction — call `get_available_llms` to list valid models. Requires
    GH_PERSONAL_ACCESS_TOKEN and an LLM provider API key.
    """
    validate_repro_id(repro_id)
    result = (
        await FetchPaperReproductionResultsSubgraph(
            github_client=_github_client(),
            litellm_client=_litellm_client(),
            llm_mapping=uniform_llm_mapping(
                FetchPaperReproductionResultsLLMMapping, model
            ),
        )
        .build_graph()
        .ainvoke(
            {
                "github_config": GitHubConfig(
                    github_owner=github_owner,
                    repository_name=repository_name,
                    branch_name=branch_name,
                ),
                "repro_id": repro_id,
            }
        )
    )
    return {
        "result": result.get("result"),
        "validation": result.get("validation"),
        "parameter_check": result.get("parameter_check"),
        "final_status": result.get("final_status"),
        "repro_md": result.get("repro_md"),
        "repro_png_base64": result.get("repro_png_base64"),
        "execution_time": result.get("execution_time"),
    }


@mcp.tool()
async def dispatch_parameter_tuning_run(
    github_owner: str,
    repository_name: str,
    branch_name: str,
    repro_id: str,
    repo_url: str = "",
    runner_label: list[str] | None = None,
) -> dict[str, Any]:
    """Start a hyperparameter tuning run for a paper reproduction (asynchronous).

    Requires a completed paper reproduction on the branch. `repro_id` is the ID
    returned by `dispatch_paper_reproduction_generate`. Returns immediately
    with `dispatched`; track progress with `get_workflow_runs` and fetch
    results with `fetch_parameter_tuning_results`. Requires
    GH_PERSONAL_ACCESS_TOKEN.
    """
    validate_repro_id(repro_id)
    result = (
        await DispatchParameterTuningRunSubgraph(
            github_client=_github_client(),
            runner_label=runner_label,
        )
        .build_graph()
        .ainvoke(
            {
                "github_config": GitHubConfig(
                    github_owner=github_owner,
                    repository_name=repository_name,
                    branch_name=branch_name,
                ),
                "repro_id": repro_id,
                "repo_url": repo_url,
            }
        )
    )
    return {"dispatched": result["dispatched"]}


@mcp.tool()
async def fetch_parameter_tuning_results(
    github_owner: str,
    repository_name: str,
    branch_name: str,
    repro_id: str,
) -> dict[str, Any]:
    """Fetch the results of a parameter tuning run.

    Use after a `dispatch_parameter_tuning_run` has succeeded. `repro_id` is
    the ID returned by `dispatch_paper_reproduction_generate`. Returns the
    tuning summary and optimization figure. Requires
    GH_PERSONAL_ACCESS_TOKEN.
    """
    validate_repro_id(repro_id)
    result = (
        await FetchParameterTuningResultsSubgraph(github_client=_github_client())
        .build_graph()
        .ainvoke(
            {
                "github_config": GitHubConfig(
                    github_owner=github_owner,
                    repository_name=repository_name,
                    branch_name=branch_name,
                ),
                "repro_id": repro_id,
            }
        )
    )
    return {
        "result": result.get("result"),
        "tuning_figure_png_base64": result.get("tuning_figure_png_base64"),
        "final_status": result.get("final_status"),
    }


# --- Prompts (guided workflows for MCP clients) ---


@mcp.prompt(title="Start an AIRAS research project")
def start_research(research_topic: str) -> str:
    """Kick off an end-to-end automated research project on a topic."""
    return f"""\
Run an end-to-end automated research project with the AIRAS MCP tools on \
this topic: {research_topic}

Follow this flow, checking in with me at each major decision:

1. Discover: generate_research_queries -> search_papers -> retrieve_papers.
2. Hypothesize & design: generate_hypothesis -> \
generate_experimental_design (ask me about the compute environment first; \
retrieve_models / retrieve_datasets list curated candidates).
3. Set up: prepare_repository, then clone the experiment repository locally.
4. Write the experiment code yourself in the clone. Read its AGENTS.md \
for the contract. For library-specific guidance, get_library_docs \
returns each library's official docs and llms.txt endpoints — fetch \
those for current API usage instead of relying on memory. Run \
mode=sanity locally until it prints SANITY_VALIDATION: PASS, then \
commit and push.
5. Run: dispatch_experiment (async). Poll get_workflow_runs or \
get_experiment_run_status between other work; debug from the stderr tail.
6. Analyze: fetch_experiment_results -> analyze_experiment (pass the code \
from the clone as {{"files": {{path: content}}}}).
7. Figures: build Vega-Lite specs and render_chart into \
.research/results/chart/, diagrams via render_diagram into \
.research/results/diagram/ (PDF, unique names), then git push. They are \
collected into the paper automatically.
8. Write: generate_bibfile -> generate_paper -> generate_latex; save the \
LaTeX as .research/latex/{{template}}/main.tex in the clone and push.
9. Publish: compile_latex (PDF on GitHub Actions) and/or open_in_overleaf \
(show me the link; local_path exports without pushing).
10. Persist: upload_research_history.

Every backend-LLM generation tool (generate_research_queries, \
generate_hypothesis, generate_experimental_design, analyze_experiment, \
generate_paper, generate_latex, compile_latex, retrieve_papers) now takes a \
required `model` argument — there is no default. Call get_available_llms \
first to see which models the configured API keys allow, and pass one; a \
model that cannot do a step's required structured output is rejected up front.

If no LLM provider key is configured, generation tools fail — in that case \
call get_generation_prompt(step, inputs) and author the artifact yourself \
following its prompt, output_json_schema, and flow.
"""


def main() -> None:
    mcp.run()


if __name__ == "__main__":
    main()
