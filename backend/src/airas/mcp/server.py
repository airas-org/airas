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

import os
import webbrowser
from typing import Any, Literal

import httpx
from mcp.server.fastmcp import FastMCP
from pydantic import BaseModel

from airas.cli import DEFAULT_DASHBOARD_PORT
from airas.core.credentials import SETUP_INSTRUCTIONS, refresh_environment
from airas.core.types.experiment_code import ExperimentCode
from airas.core.types.experiment_history import ExperimentHistory
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
from airas.core.types.wandb import WandbConfig
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
from airas.infra.langchain_client import (
    PROVIDER_REQUIRED_ENV_VARS,
    LangChainClient,
)
from airas.infra.llm_provider_resolver import detect_available_providers
from airas.infra.openalex_client import OpenAlexClient
from airas.infra.semantic_scholar_client import SemanticScholarClient
from airas.usecases.analyzers.analyze_experiment_subgraph.analyze_experiment_subgraph import (
    AnalyzeExperimentSubgraph,
)
from airas.usecases.executors.dispatch_experiment_on_static_runner_subgraph.dispatch_experiment_on_static_runner_subgraph import (
    DispatchExperimentOnStaticRunnerSubgraph,
)
from airas.usecases.executors.dispatch_visualization_subgraph.dispatch_visualization_subgraph import (
    DispatchVisualizationSubgraph,
)
from airas.usecases.executors.fetch_experiment_code_subgraph.fetch_experiment_code_subgraph import (
    FetchExperimentCodeSubgraph,
)
from airas.usecases.executors.fetch_experiment_results_subgraph.fetch_experiment_results_subgraph import (
    FetchExperimentResultsSubgraph,
)
from airas.usecases.executors.fetch_run_ids_subgraph.fetch_run_ids_subgraph import (
    FetchRunIdsSubgraph,
)
from airas.usecases.generators.dispatch_code_generation_subgraph.dispatch_code_generation_subgraph import (
    DispatchCodeGenerationSubgraph,
)
from airas.usecases.generators.dispatch_diagram_generation_subgraph.dispatch_diagram_generation_subgraph import (
    DispatchDiagramGenerationSubgraph,
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
from airas.usecases.generators.refine_experimental_design_subgraph.refine_experimental_design_subgraph import (
    RefineExperimentalDesignSubgraph,
)
from airas.usecases.github.download_github_actions_artifacts_subgraph.download_github_actions_artifacts_subgraph import (
    DownloadGithubActionsArtifactsSubgraph,
)
from airas.usecases.github.github_download_subgraph import GithubDownloadSubgraph
from airas.usecases.github.github_upload_subgraph import GithubUploadSubgraph
from airas.usecases.github.prepare_repository_subgraph.prepare_repository_subgraph import (
    PrepareRepositorySubgraph,
)
from airas.usecases.github.push_github_subgraph.push_github_subgraph import (
    PushGitHubSubgraph,
)
from airas.usecases.github.set_github_actions_secrets_subgraph.set_github_actions_secrets_subgraph import (
    SetGithubActionsSecretsSubgraph,
)
from airas.usecases.publication.compile_latex_subgraph.compile_latex_subgraph import (
    CompileLatexSubgraph,
)
from airas.usecases.publication.generate_latex_subgraph.generate_latex_subgraph import (
    GenerateLatexSubgraph,
)
from airas.usecases.publication.push_latex_subgraph.push_latex_subgraph import (
    PushLatexSubgraph,
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
async def generate_research_queries(
    research_topic: str,
    num_queries: int = 2,
) -> list[str]:
    """Generate academic paper search queries from a research topic.

    Use this first to turn a free-form research topic into effective
    search queries, then pass them to `search_papers`.
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
    """Generate a novel research hypothesis from a topic and related studies.

    `research_study_list` should be the output of `retrieve_papers`. Higher
    `refinement_rounds` improves quality at the cost of more LLM calls.
    Requires an LLM provider API key.
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
    """Design experiments to test a research hypothesis.

    `research_hypothesis` should be the output of `generate_hypothesis`.
    `compute_environment` optionally describes the hardware the experiments
    will run on (e.g. {"gpu_type": "A100", "gpu_count": 1}); it constrains
    the design to what is actually runnable. Requires an LLM provider API key.
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
async def refine_experimental_design(
    research_hypothesis: dict[str, Any],
    experiment_history: dict[str, Any],
    design_instruction: str,
    compute_environment: dict[str, Any] | None = None,
    num_models_to_use: int = 1,
    num_datasets_to_use: int = 1,
    num_comparative_methods: int = 1,
) -> dict[str, Any]:
    """Refine an experimental design based on results so far and an instruction.

    Use after experiments have run: `experiment_history` carries the designs
    and results accumulated so far, and `design_instruction` states what to
    change (e.g. "add an ablation for the attention variant"). Returns the
    revised experimental design. Requires an LLM provider API key.
    """
    env = ComputeEnvironment.model_validate(compute_environment or {})
    result = (
        await RefineExperimentalDesignSubgraph(
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
                "experiment_history": ExperimentHistory.model_validate(
                    experiment_history
                ),
                "design_instruction": design_instruction,
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
async def set_github_actions_secrets(
    github_owner: str,
    repository_name: str,
    branch_name: str = "main",
) -> dict[str, Any]:
    """Copy required secrets (LLM API keys etc.) from local environment variables to the experiment repository's GitHub Actions secrets.

    Run this after `prepare_repository` so that code generation and
    experiment workflows can call LLM providers. Requires GH_PERSONAL_ACCESS_TOKEN.
    """
    config = GitHubConfig(
        github_owner=github_owner,
        repository_name=repository_name,
        branch_name=branch_name,
    )
    result = (
        await SetGithubActionsSecretsSubgraph(github_client=_github_client())
        .build_graph()
        .ainvoke({"github_config": config})
    )
    return {"secrets_set": result["secrets_set"]}


@mcp.tool()
async def dispatch_code_generation(
    github_owner: str,
    repository_name: str,
    branch_name: str,
    research_topic: str,
    research_hypothesis: dict[str, Any],
    experimental_design: dict[str, Any],
    wandb_entity: str,
    wandb_project: str,
    github_actions_agent: Literal["claude_code", "open_code"] = "open_code",
) -> dict[str, Any]:
    """Start experiment-code generation on GitHub Actions (asynchronous).

    Dispatches a workflow in the experiment repository that generates the
    experiment code with a coding agent. Returns immediately with
    `dispatched`; track progress with `get_workflow_runs` and fetch the
    generated code with `fetch_experiment_code` once the run succeeds.
    Requires GH_PERSONAL_ACCESS_TOKEN and an LLM provider API key.
    """
    result = (
        await DispatchCodeGenerationSubgraph(
            github_client=_github_client(),
            llm_mapping=None,
        )
        .build_graph()
        .ainvoke(
            {
                "github_config": GitHubConfig(
                    github_owner=github_owner,
                    repository_name=repository_name,
                    branch_name=branch_name,
                ),
                "research_topic": research_topic,
                "research_hypothesis": ResearchHypothesis.model_validate(
                    research_hypothesis
                ),
                "experimental_design": ExperimentalDesign.model_validate(
                    experimental_design
                ),
                "wandb_config": WandbConfig(entity=wandb_entity, project=wandb_project),
                "github_actions_agent": github_actions_agent,
            }
        )
    )
    return {"dispatched": result["dispatched"]}


@mcp.tool()
async def dispatch_experiment(
    github_owner: str,
    repository_name: str,
    branch_name: str,
    run_id: str,
    workflow: Literal["sanity_check", "main"] = "sanity_check",
    runner_label: list[str] | None = None,
) -> dict[str, Any]:
    """Start an experiment run on GitHub Actions (asynchronous).

    `workflow` selects the stage: "sanity_check" for a quick correctness run,
    "main" for the full experiment. `run_id` identifies the experiment run
    defined by the generated code. Returns immediately with `dispatched`;
    track progress with `get_workflow_runs` and collect outputs with
    `fetch_experiment_results`. Requires GH_PERSONAL_ACCESS_TOKEN.
    """
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
    return {"dispatched": result["dispatched"]}


@mcp.tool()
async def get_workflow_runs(
    github_owner: str,
    repository_name: str,
    branch_name: str | None = None,
    limit: int = 5,
) -> list[dict[str, Any]]:
    """Check the status of recent GitHub Actions runs in the experiment repository (non-blocking).

    Returns the most recent dispatched workflow runs with their status and
    conclusion. Use this to track runs started by `dispatch_code_generation`
    or `dispatch_experiment` — poll it between other work instead of waiting.
    Requires GH_PERSONAL_ACCESS_TOKEN.
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
async def fetch_experiment_code(
    github_owner: str,
    repository_name: str,
    branch_name: str,
) -> dict[str, Any]:
    """Fetch the generated experiment code from the experiment repository.

    Use after a `dispatch_code_generation` run has succeeded. The returned
    object can be passed to `analyze_experiment` as `experiment_code`.
    Requires GH_PERSONAL_ACCESS_TOKEN.
    """
    result = (
        await FetchExperimentCodeSubgraph(github_client=_github_client())
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
    return _dump(result["experiment_code"])


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
    `fetch_experiment_code`, and `fetch_experiment_results`, and returns a
    structured analysis (findings, whether the hypothesis is supported, and
    suggested next steps). Requires an LLM provider API key.
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


@mcp.tool()
async def fetch_run_ids(
    github_owner: str,
    repository_name: str,
    branch_name: str,
) -> list[str]:
    """List the experiment run IDs recorded in the experiment repository.

    Run IDs identify individual experiment runs defined by the generated
    code; pass them to `dispatch_experiment` or `dispatch_visualization`.
    Requires GH_PERSONAL_ACCESS_TOKEN.
    """
    result = (
        await FetchRunIdsSubgraph(github_client=_github_client())
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
    return result["run_ids"]


@mcp.tool()
async def dispatch_visualization(
    github_owner: str,
    repository_name: str,
    branch_name: str,
    run_ids: list[str],
    runner_label: list[str] | None = None,
) -> dict[str, Any]:
    """Start result-visualization generation on GitHub Actions (asynchronous).

    Generates figures for the given experiment `run_ids` (from
    `fetch_run_ids`). The figures are used by the paper-writing stage.
    Returns immediately; track with `get_workflow_runs`.
    Requires GH_PERSONAL_ACCESS_TOKEN.
    """
    result = (
        await DispatchVisualizationSubgraph(
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
                "run_ids": run_ids,
            }
        )
    )
    return {"dispatched": result["dispatched"]}


@mcp.tool()
async def dispatch_diagram_generation(
    github_owner: str,
    repository_name: str,
    branch_name: str,
    github_actions_agent: Literal["claude_code", "open_code"] = "claude_code",
    diagram_description: str | None = None,
) -> dict[str, Any]:
    """Start method-diagram generation on GitHub Actions (asynchronous).

    Generates an explanatory diagram of the proposed method for the paper.
    `diagram_description` optionally guides what the diagram should show.
    Returns immediately; track with `get_workflow_runs`.
    Requires GH_PERSONAL_ACCESS_TOKEN.
    """
    result = (
        await DispatchDiagramGenerationSubgraph(
            github_client=_github_client(),
            diagram_description=diagram_description,
            prompt_path=None,
            llm_mapping=None,
        )
        .build_graph()
        .ainvoke(
            {
                "github_config": GitHubConfig(
                    github_owner=github_owner,
                    repository_name=repository_name,
                    branch_name=branch_name,
                ),
                "github_actions_agent": github_actions_agent,
            }
        )
    )
    return {"dispatched": result["dispatched"]}


@mcp.tool()
async def push_files(
    github_owner: str,
    repository_name: str,
    branch_name: str,
    files: dict[str, str],
) -> dict[str, Any]:
    """Push files to the experiment repository.

    `files` maps repository paths to file contents (text). Useful for
    manual fixes to experiment code or configuration between runs.
    Requires GH_PERSONAL_ACCESS_TOKEN.
    """
    result = (
        await PushGitHubSubgraph(github_client=_github_client())
        .build_graph()
        .ainvoke(
            {
                "github_config": GitHubConfig(
                    github_owner=github_owner,
                    repository_name=repository_name,
                    branch_name=branch_name,
                ),
                "push_files": files,
            }
        )
    )
    return {"is_file_pushed": result["is_file_pushed"]}


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
    """Write the paper content from the completed research.

    Takes the hypothesis, experiment history, experiment code, related
    studies, and the BibTeX file (from `generate_bibfile`), and produces
    structured paper content (title, abstract, sections). Pass the result
    to `generate_latex`. Requires an LLM provider API key.
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
    """Convert paper content into a full LaTeX document.

    `paper_content` should be the output of `generate_paper`. Available
    templates: "mdpi", "iclr2024", "agents4science_2025". Push the returned
    LaTeX to the experiment repository with `push_latex`, then build the PDF
    with `compile_latex`. Requires an LLM provider API key and
    GH_PERSONAL_ACCESS_TOKEN.
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
async def push_latex(
    github_owner: str,
    repository_name: str,
    branch_name: str,
    latex_text: str,
    latex_template_name: LATEX_TEMPLATE_NAME = "mdpi",
) -> dict[str, Any]:
    """Push the LaTeX document and figures to the experiment repository.

    Uploads the LaTeX source (from `generate_latex`) and prepares the images
    so that `compile_latex` can build the PDF. Requires GH_PERSONAL_ACCESS_TOKEN.
    """
    result = (
        await PushLatexSubgraph(
            github_client=_github_client(),
            latex_template_name=latex_template_name,
        )
        .build_graph()
        .ainvoke(
            {
                "github_config": GitHubConfig(
                    github_owner=github_owner,
                    repository_name=repository_name,
                    branch_name=branch_name,
                ),
                "latex_text": latex_text,
            }
        )
    )
    return {
        "is_upload_successful": result["is_upload_successful"],
        "is_images_prepared": result["is_images_prepared"],
    }


@mcp.tool()
async def compile_latex(
    github_owner: str,
    repository_name: str,
    branch_name: str,
    latex_template_name: LATEX_TEMPLATE_NAME = "mdpi",
    github_actions_agent: Literal["claude_code", "open_code"] = "claude_code",
) -> dict[str, Any]:
    """Build the paper PDF on GitHub Actions (asynchronous).

    Dispatches the LaTeX compilation workflow for the sources pushed by
    `push_latex`. Returns immediately with `paper_url` (when available);
    track the run with `get_workflow_runs`. Requires GH_PERSONAL_ACCESS_TOKEN.
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


def main() -> None:
    mcp.run()


if __name__ == "__main__":
    main()
