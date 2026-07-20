"""AIRAS MCP server (stdio).

Exposes AIRAS research subgraphs as MCP tools for use from MCP clients
such as Claude Code and Claude Desktop.

Credentials are read from ~/.airas/credentials.json (see credentials.py):
- LLM providers: OPENAI_API_KEY / ANTHROPIC_API_KEY / GEMINI_API_KEY (at least one)
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
from pydantic import BaseModel

from airas.cli import DEFAULT_DASHBOARD_PORT
from airas.core.credentials import SETUP_INSTRUCTIONS, refresh_environment
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
from airas.core.types.paper import PaperContent
from airas.core.types.paper_search import PAPER_SEARCH_SOURCES
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
from airas.infra.aixs_client import AixsClient
from airas.infra.arxiv_client import ArxivClient
from airas.infra.github_client import GithubClient
from airas.infra.kroki_client import KrokiClient
from airas.infra.langchain_client import (
    PROVIDER_REQUIRED_ENV_VARS,
    LangChainClient,
)
from airas.infra.llm_provider_resolver import detect_available_providers
from airas.infra.openalex_client import OpenAlexClient
from airas.infra.retry_policy import HTTPClientFatalError, HTTPClientRetryableError
from airas.infra.semantic_scholar_client import SemanticScholarClient
from airas.mcp.prompt_registry import build_generation_prompt
from airas.resources.libraries.library_docs import LIBRARY_DOCS
from airas.usecases.analyzers.analyze_experiment_subgraph.analyze_experiment_subgraph import (
    AnalyzeExperimentSubgraph,
)
from airas.usecases.executors.dispatch_experiment_on_aixs_subgraph.dispatch_experiment_on_aixs_subgraph import (
    DispatchExperimentOnAixsSubgraph,
)
from airas.usecases.executors.dispatch_experiment_on_static_runner_subgraph.dispatch_experiment_on_static_runner_subgraph import (
    DispatchExperimentOnStaticRunnerSubgraph,
)
from airas.usecases.executors.fetch_experiment_results_subgraph.fetch_experiment_results_subgraph import (
    FetchExperimentResultsSubgraph,
)
from airas.usecases.generators.generate_experimental_design_subgraph.generate_experimental_design_subgraph import (
    GenerateExperimentalDesignSubgraph,
)
from airas.usecases.generators.generate_hypothesis_subgraph.generate_hypothesis_subgraph_v0 import (
    GenerateHypothesisSubgraphV0,
)
from airas.usecases.generators.generate_queries_subgraph.generate_queries_subgraph import (
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
    CompileLatexSubgraph,
)
from airas.usecases.publication.generate_latex_subgraph.generate_latex_subgraph import (
    GenerateLatexSubgraph,
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
)
from airas.usecases.retrieve.search_paper_titles_subgraph.nodes.search_paper_titles_from_airas_db import (
    AirasDbPaperSearchIndex,
)
from airas.usecases.retrieve.search_papers_subgraph.search_papers_subgraph import (
    SearchPapersSubgraph,
)
from airas.usecases.writers.generate_bibfile_subgraph.generate_bibfile_subgraph import (
    GenerateBibfileSubgraph,
)
from airas.usecases.writers.write_subgraph.write_subgraph import WriteSubgraph

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


def _aixs_client() -> AixsClient:
    refresh_environment()
    if not os.getenv("AIXS_API_KEY"):
        raise RuntimeError(f"AIXS_API_KEY is not configured. {SETUP_INSTRUCTIONS}")
    return AixsClient(sync_session=_sync_session, async_session=_async_session)


def _kroki_client() -> KrokiClient:
    refresh_environment()
    return KrokiClient(sync_session=_sync_session, async_session=_async_session)


def _arxiv_client() -> ArxivClient:
    return ArxivClient(sync_session=_sync_session, async_session=_async_session)


def _openalex_client() -> OpenAlexClient:
    refresh_environment()  # OPENALEX_API_KEY is optional
    return OpenAlexClient(sync_session=_sync_session, async_session=_async_session)


def _semantic_scholar_client() -> SemanticScholarClient:
    refresh_environment()  # SEMANTIC_SCHOLAR_API_KEY is optional
    return SemanticScholarClient(
        sync_session=_sync_session, async_session=_async_session
    )


def _langchain_client() -> LangChainClient:
    refresh_environment()
    if not detect_available_providers(PROVIDER_REQUIRED_ENV_VARS):
        raise RuntimeError(
            f"No LLM provider API keys are configured. {SETUP_INSTRUCTIONS}"
        )
    return LangChainClient()


def _dump(value: Any) -> Any:
    return value.model_dump() if isinstance(value, BaseModel) else value


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

    Returns a fully rendered `prompt`, an `output_json_schema` describing
    exactly the data format to produce in one pass, and a `flow` note on
    how the output feeds the next step.
    """
    return build_generation_prompt(step, inputs)


@mcp.tool()
async def generate_research_queries(
    research_topic: str,
    num_queries: int = 2,
) -> list[str]:
    """Generate academic paper search queries from a research topic (backend LLM).

    Use this first to turn a free-form research topic into effective
    search queries, then pass them to `search_papers`. Requires an LLM
    provider API key — without one, use
    `get_generation_prompt(step="research_queries", ...)` and author the
    queries yourself.
    """
    result = (
        await GenerateQueriesSubgraph(
            llm_client=_langchain_client(),
            num_paper_search_queries=num_queries,
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
) -> dict[str, Any]:
    """Fetch the full text of a paper by arXiv ID, DOI, or direct PDF URL.

    Provide one identifier (tried in that order). arXiv IDs are fetched from
    arXiv; DOIs are resolved to an open-access PDF via Semantic Scholar.
    Returns the extracted text with `status`: "fulltext", "abstract_only"
    (no legal open-access PDF found, abstract returned instead), or
    "not_found". No API keys required.
    """
    if not (arxiv_id or doi or pdf_url):
        raise ValueError("One of arxiv_id, doi, or pdf_url must be provided.")
    refresh_environment()
    result = (
        await FetchPaperFulltextSubgraph(
            semantic_scholar_client=_semantic_scholar_client(),
        )
        .build_graph()
        .ainvoke({"arxiv_id": arxiv_id, "doi": doi, "pdf_url": pdf_url})
    )
    return {
        "text": result["text"],
        "status": result["status"],
        "resolved_from": result["resolved_from"],
    }


@mcp.tool()
async def retrieve_papers(paper_titles: list[str]) -> list[dict[str, Any]]:
    """Retrieve full paper information for the given titles.

    Fetches each paper (via arXiv) and extracts structured research study
    data: abstract, methods, experimental settings, and results. The returned
    objects can be passed to `generate_hypothesis` as `research_study_list`.
    Requires GH_PERSONAL_ACCESS_TOKEN and an LLM provider API key.
    """
    result = (
        await RetrievePaperSubgraph(
            langchain_client=_langchain_client(),
            arxiv_client=_arxiv_client(),
            github_client=_github_client(),
            llm_mapping=None,
        )
        .build_graph()
        .ainvoke({"paper_titles": paper_titles})
    )
    return [study.model_dump() for study in result["research_study_list"]]


@mcp.tool()
async def generate_hypothesis(
    research_topic: str,
    research_study_list: list[dict[str, Any]],
    refinement_rounds: int = 1,
) -> dict[str, Any]:
    """Generate a novel research hypothesis from a topic and related studies (backend LLM).

    `research_study_list` should be the output of `retrieve_papers`. Higher
    `refinement_rounds` improves quality at the cost of more LLM calls.
    Requires an LLM provider API key — without one, use
    `get_generation_prompt(step="hypothesis", ...)` and author the
    hypothesis yourself.
    """
    studies = [ResearchStudy.model_validate(study) for study in research_study_list]
    result = (
        await GenerateHypothesisSubgraphV0(
            langchain_client=_langchain_client(),
            refinement_rounds=refinement_rounds,
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
    compute_environment: dict[str, Any] | None = None,
    num_models_to_use: int = 1,
    num_datasets_to_use: int = 1,
    num_comparative_methods: int = 1,
) -> dict[str, Any]:
    """Design experiments to test a research hypothesis (backend LLM).

    `research_hypothesis` should be the output of `generate_hypothesis`.
    `compute_environment` optionally describes the hardware the experiments
    will run on (e.g. {"gpu_type": "A100", "gpu_count": 1}); it constrains
    the design to what is actually runnable. Requires an LLM provider API
    key — without one, use
    `get_generation_prompt(step="experimental_design", ...)` and author the
    design yourself.
    """
    env = ComputeEnvironment.model_validate(compute_environment or {})
    result = (
        await GenerateExperimentalDesignSubgraph(
            langchain_client=_langchain_client(),
            compute_environment=env,
            num_models_to_use=num_models_to_use,
            num_datasets_to_use=num_datasets_to_use,
            num_comparative_methods=num_comparative_methods,
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
    """List curated candidate models for experiments in the given subfield.

    Subfields: "transformer_decoder_based_models", "image_models",
    "multi_modal_models", "llm_api_models". Returns model configurations
    usable in an experimental design. No API keys required.
    """
    result = (
        await RetrieveModelsSubgraph()
        .build_graph()
        .ainvoke({"model_subfield": model_subfield})
    )
    return result["models_dict"]


@mcp.tool()
async def retrieve_datasets(dataset_subfield: DatasetSubfield) -> dict[str, Any]:
    """List curated candidate datasets for experiments in the given subfield.

    Subfields: "language_model_fine_tuning_datasets", "image_datasets",
    "prompt_engineering_datasets". Returns dataset configurations usable in
    an experimental design. No API keys required.
    """
    result = (
        await RetrieveDatasetsSubgraph()
        .build_graph()
        .ainvoke({"dataset_subfield": dataset_subfield})
    )
    return result["datasets_dict"]


@mcp.tool()
def get_library_docs(
    library: str | None = None, category: str | None = None
) -> dict[str, Any]:
    """Look up canonical documentation endpoints for AI research libraries.

    Covers ~125 libraries across the research stack: fine-tuning,
    post-training, distributed training, inference serving, GPU computing,
    interpretability, RL and simulation, vision/audio, JAX, RAG, structured
    output, evaluation, data processing, statistics, Bayesian inference,
    mathematical optimization, causal inference, time series, quantum
    computing, and more. For each library
    returns the official docs URL, the GitHub repository, and — where the
    project publishes one — its `llms.txt` / `llms-full.txt` endpoint, which
    serves the current documentation in a machine-readable form. Fetch those
    endpoints to get up-to-date library guidance while writing experiment
    code. Pass `library` for one entry; `category` to list one category;
    no arguments to list everything. No API keys required.
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
        name: {"description": e["description"], "category": e["category"]}
        for name, e in LIBRARY_DOCS.items()
        if category is None or e["category"] == category
    }
    if not listing:
        return {
            "error": f"Unknown category: {category!r}.",
            "available": sorted({e["category"] for e in LIBRARY_DOCS.values()}),
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
    }


@mcp.tool()
async def dispatch_experiment(
    github_owner: str,
    repository_name: str,
    branch_name: str,
    run_id: str,
    workflow: Literal["sanity_check", "main"] = "sanity_check",
    runner_label: list[str] | None = None,
    backend: Literal["github_actions", "aixs"] = "github_actions",
    compute_type: str = "gpu-a10",
) -> dict[str, Any]:
    """Start an experiment run (asynchronous). The code must already be pushed.

    `workflow` selects the stage: "sanity_check" for a quick correctness run,
    "main" for the full experiment. `run_id` identifies the experiment run
    defined by the experiment code (one config/run/{run_id}.yaml).

    `backend` selects where the run executes:
    - "github_actions" (default): dispatches a workflow in the experiment
      repository. `runner_label` picks the runner. Track progress with
      `get_workflow_runs` and collect outputs with `fetch_experiment_results`.
      Requires GH_PERSONAL_ACCESS_TOKEN.
    - "aixs": executes on the AIXS compute platform (GPU without GitHub
      Actions limits). `compute_type` picks the machine (e.g. "cpu-general",
      "gpu-a10"). Requires AIXS_API_KEY, and W&B API keys must be registered
      as env vars on the AIXS side.

    Track progress and fetch execution errors with
    `get_experiment_run_status`. For "aixs" the returned `execution_id` is
    passed directly; for "github_actions" the workflow-dispatch API returns
    no id, so discover the run id with `get_workflow_runs` first.
    """
    if backend == "aixs":
        run_stage = RunStage.SANITY if workflow == "sanity_check" else RunStage.FULL
        aixs_result = (
            await DispatchExperimentOnAixsSubgraph(
                aixs_client=_aixs_client(),
                run_stage=run_stage,
                compute_type=compute_type,
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
            "dispatched": aixs_result["dispatched"],
            "backend": "aixs",
            "execution_id": aixs_result["aixs_run_id"],
            "execution_url": aixs_result["aixs_run_url"],
        }

    workflow_file = (
        "run_sanity_check.yml"
        if workflow == "sanity_check"
        else "run_main_experiment.yml"
    )
    result = (
        await DispatchExperimentOnStaticRunnerSubgraph(
            github_client=_github_client(),
            workflow_file=workflow_file,
            runner_label=runner_label or ["ubuntu-latest"],
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
    backend: Literal["github_actions", "aixs"] = "github_actions",
    github_owner: str | None = None,
    repository_name: str | None = None,
    log_tail_lines: int = 200,
) -> dict[str, Any]:
    """Check one experiment run and fetch its execution logs (non-blocking).

    `execution_id` identifies the run on the selected `backend`: the
    `execution_id` returned by `dispatch_experiment(backend="aixs")`, or a
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

    client = _aixs_client()
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
) -> dict[str, Any]:
    """Analyze experiment results against the hypothesis and design.

    Takes the outputs of `generate_hypothesis`, `generate_experimental_design`,
    and `fetch_experiment_results`, and returns a structured analysis
    (findings, whether the hypothesis is supported, and suggested next
    steps). For `experiment_code`, read the code from your local clone and
    pass `{"files": {"<relative path>": "<content>", ...}}`.
    Requires an LLM provider API key — without one, use
    `get_generation_prompt(step="experiment_analysis", ...)` and write the
    analysis yourself.
    """
    result = (
        await AnalyzeExperimentSubgraph(
            langchain_client=_langchain_client(),
            llm_mapping=None,
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


@mcp.tool()
async def upload_research_history(
    github_owner: str,
    repository_name: str,
    branch_name: str,
    research_history: dict[str, Any],
    commit_message: str | None = None,
) -> dict[str, Any]:
    """Save research history (hypothesis, design, results, ...) to the experiment repository.

    AIRAS persists research state in the GitHub repository, so uploading the
    accumulated history lets you resume work in a later session with
    `download_research_history`. Requires GH_PERSONAL_ACCESS_TOKEN.
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
                "research_history": ResearchHistory.model_validate(research_history),
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
) -> dict[str, Any]:
    """Render a Vega-Lite spec to a chart file, entirely locally.

    Use this for publication-quality result figures: build a Vega-Lite JSON
    spec from the experiment results (inline the data under `data.values`).
    When rendering into a local clone of the experiment repository, save
    the chart as a PDF under `.research/results/chart/`, then commit and
    push — the LaTeX build collects every `*.pdf` under
    `.research/results/`. `output_path` must end with .pdf, .svg, or .png.
    Rendering runs in-process (vl-convert); no data leaves the machine and
    no API keys are required.
    """
    path, suffix = _resolve_render_output(output_path)
    if suffix == "pdf":
        data = await asyncio.to_thread(vlc.vegalite_to_pdf, vega_lite_spec)
    elif suffix == "svg":
        svg = await asyncio.to_thread(vlc.vegalite_to_svg, vega_lite_spec)
        data = svg.encode("utf-8")
    else:
        data = await asyncio.to_thread(vlc.vegalite_to_png, vega_lite_spec)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)
    return {"output_path": str(path), "bytes_written": len(data)}


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
    writing_refinement_rounds: int = 2,
) -> dict[str, Any]:
    """Write the paper content from the completed research (backend LLM).

    Takes the hypothesis, experiment history, experiment code, related
    studies, and the BibTeX file (from `generate_bibfile`), and produces
    structured paper content (title, abstract, sections). Pass the result
    to `generate_latex`. Requires an LLM provider API key — without one, use
    `get_generation_prompt(step="paper_writing", ...)` and author the paper
    yourself in one pass with the same curated prompt.
    """
    result = (
        await WriteSubgraph(
            langchain_client=_langchain_client(),
            paper_content_refinement_iterations=writing_refinement_rounds,
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
    latex_template_name: LATEX_TEMPLATE_NAME = "mdpi",
) -> str:
    """Convert paper content into a full LaTeX document (backend LLM).

    `paper_content` should be the output of `generate_paper`. Available
    templates: "mdpi", "iclr2024", "agents4science_2025". Write the returned
    LaTeX to `.research/latex/{template}/main.tex` in your local clone of
    the experiment repository and push it with git, then build the PDF with
    `compile_latex` and/or hand it over with `open_in_overleaf`. Requires an
    LLM provider API key and GH_PERSONAL_ACCESS_TOKEN — without them, use
    `get_generation_prompt(step="latex_conversion", ...)` and do the
    conversion yourself with the template from your local clone.
    """
    result = (
        await GenerateLatexSubgraph(
            langchain_client=_langchain_client(),
            github_client=_github_client(),
            latex_template_name=latex_template_name,
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
    latex_template_name: LATEX_TEMPLATE_NAME = "mdpi",
    github_actions_agent: Literal["claude_code", "open_code"] = "claude_code",
) -> dict[str, Any]:
    """Build the paper PDF on GitHub Actions (asynchronous).

    One of the two publication exits after main.tex has been pushed to
    `.research/latex/{template}/` (the other is `open_in_overleaf`; they
    are independent and can both be used).
    Dispatches the LaTeX compilation workflow for the pushed sources;
    figure PDFs under `.research/results/` and `.research/diagrams/` are
    materialized into `images/` at build time. Returns immediately with
    `paper_url` (when available); track the run with `get_workflow_runs`.
    Requires GH_PERSONAL_ACCESS_TOKEN.
    """
    result = (
        await CompileLatexSubgraph(
            github_client=_github_client(),
            latex_template_name=latex_template_name,
            github_actions_agent=github_actions_agent,
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

If an LLM provider key is missing, generation tools fail — in that case \
call get_generation_prompt(step, inputs) and author the artifact yourself \
following its prompt, output_json_schema, and flow.
"""


def main() -> None:
    mcp.run()


if __name__ == "__main__":
    main()
