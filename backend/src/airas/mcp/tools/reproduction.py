"""Paper reproduction and parameter tuning."""

from typing import Any, Literal

from airas.core.llm_config import uniform_llm_mapping
from airas.core.types.github import GitHubConfig
from airas.mcp.app import mcp
from airas.mcp.context import (
    _github_client,
    _litellm_client,
)
from airas.workflows.execution.dispatch_paper_reproduction_run_subgraph.dispatch_paper_reproduction_run_subgraph import (
    DispatchPaperReproductionRunSubgraph,
)
from airas.workflows.execution.dispatch_parameter_tuning_run_subgraph.dispatch_parameter_tuning_run_subgraph import (
    DispatchParameterTuningRunSubgraph,
)
from airas.workflows.execution.fetch_paper_reproduction_results_subgraph.fetch_paper_reproduction_results_subgraph import (
    FetchPaperReproductionResultsLLMMapping,
    FetchPaperReproductionResultsSubgraph,
)
from airas.workflows.execution.fetch_parameter_tuning_results_subgraph.fetch_parameter_tuning_results_subgraph import (
    FetchParameterTuningResultsSubgraph,
)
from airas.workflows.generators.dispatch_paper_reproduction_generate_subgraph.dispatch_paper_reproduction_generate_subgraph import (
    DispatchPaperReproductionGenerateLLMMapping,
    DispatchPaperReproductionGenerateSubgraph,
)
from airas.workflows.generators.dispatch_paper_reproduction_generate_subgraph.repro_id import (
    validate_repro_id,
)


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
