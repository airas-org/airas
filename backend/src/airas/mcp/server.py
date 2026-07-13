"""AIRAS MCP server (stdio).

Exposes AIRAS research subgraphs as MCP tools for use from MCP clients
such as Claude Code and Claude Desktop.

Credentials are read from environment variables:
- LLM providers: OPENAI_API_KEY / ANTHROPIC_API_KEY / GEMINI_API_KEY (at least one)
- GitHub (repository/experiment tools): GH_PERSONAL_ACCESS_TOKEN

Run locally:
    uvx --from "airas[mcp]" airas-mcp
"""

import os
from typing import Any, Literal

from mcp.server.fastmcp import FastMCP
from pydantic import BaseModel

from airas.core.types.experiment_code import ExperimentCode
from airas.core.types.experiment_history import ExperimentHistory
from airas.core.types.experimental_design import ComputeEnvironment, ExperimentalDesign
from airas.core.types.experimental_results import ExperimentalResults
from airas.core.types.github import GitHubConfig
from airas.core.types.latex import LATEX_TEMPLATE_NAME
from airas.core.types.paper import PaperContent
from airas.core.types.research_history import ResearchHistory
from airas.core.types.research_hypothesis import ResearchHypothesis
from airas.core.types.research_study import ResearchStudy
from airas.core.types.wandb import WandbConfig
from airas.infra.arxiv_client import ArxivClient
from airas.infra.github_client import GithubClient
from airas.infra.langchain_client import LangChainClient
from airas.usecases.analyzers.analyze_experiment_subgraph.analyze_experiment_subgraph import (
    AnalyzeExperimentSubgraph,
)
from airas.usecases.executors.dispatch_experiment_on_static_runner_subgraph.dispatch_experiment_on_static_runner_subgraph import (
    DispatchExperimentOnStaticRunnerSubgraph,
)
from airas.usecases.executors.fetch_experiment_code_subgraph.fetch_experiment_code_subgraph import (
    FetchExperimentCodeSubgraph,
)
from airas.usecases.executors.fetch_experiment_results_subgraph.fetch_experiment_results_subgraph import (
    FetchExperimentResultsSubgraph,
)
from airas.usecases.generators.dispatch_code_generation_subgraph.dispatch_code_generation_subgraph import (
    DispatchCodeGenerationSubgraph,
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
from airas.usecases.retrieve.retrieve_paper_subgraph.retrieve_paper_subgraph import (
    RetrievePaperSubgraph,
)
from airas.usecases.retrieve.search_paper_titles_subgraph.nodes.search_paper_titles_from_airas_db import (
    AirasDbPaperSearchIndex,
)
from airas.usecases.retrieve.search_paper_titles_subgraph.search_paper_titles_from_airas_db_subgraph import (
    SearchPaperTitlesFromAirasDbSubgraph,
)
from airas.usecases.writers.generate_bibfile_subgraph.generate_bibfile_subgraph import (
    GenerateBibfileSubgraph,
)
from airas.usecases.writers.write_subgraph.write_subgraph import WriteSubgraph

mcp = FastMCP("airas")

# BM25 index over the AIRAS papers DB; built lazily on first search and
# reused for the lifetime of the server process.
_search_index = AirasDbPaperSearchIndex()


def _github_client() -> GithubClient:
    token = os.getenv("GH_PERSONAL_ACCESS_TOKEN", "")
    if not token:
        raise RuntimeError(
            "GH_PERSONAL_ACCESS_TOKEN environment variable is not set. "
            "Set it in the `env` block of your MCP client configuration."
        )
    return GithubClient(github_token=token)


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
    search queries, then pass them to `search_paper_titles`.
    """
    result = (
        await GenerateQueriesSubgraph(
            llm_client=LangChainClient(),
            num_paper_search_queries=num_queries,
        )
        .build_graph()
        .ainvoke({"research_topic": research_topic})
    )
    return result["queries"]


@mcp.tool()
async def search_paper_titles(
    queries: list[str],
    max_results_per_query: int = 3,
) -> list[str]:
    """Search the AIRAS papers database (major ML conferences) for paper titles.

    Takes search queries (e.g. from `generate_research_queries`) and returns
    matching paper titles. The first call builds the search index, which can
    take a while; subsequent calls are fast. No API keys required.
    """
    result = (
        await SearchPaperTitlesFromAirasDbSubgraph(
            search_index=_search_index,
            papers_per_query=max_results_per_query,
        )
        .build_graph()
        .ainvoke({"queries": queries})
    )
    return result["paper_titles"]


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
            langchain_client=LangChainClient(),
            arxiv_client=ArxivClient(),
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
            langchain_client=LangChainClient(),
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
            langchain_client=LangChainClient(),
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
            langchain_client=LangChainClient(),
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
            langchain_client=LangChainClient(),
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
            langchain_client=LangChainClient(),
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


def main() -> None:
    mcp.run()


if __name__ == "__main__":
    main()
