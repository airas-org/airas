"""Paper reproduction and parameter tuning."""

import time
from typing import Any, Literal

from airas.core.llm_config import NodeLLMConfig
from airas.core.types.github import GitHubConfig
from airas.mcp.app import mcp
from airas.mcp.context import (
    _github_client,
    _litellm_client,
)
from airas.usecases.reproduction.dispatch_paper_reproduction_generate import (
    dispatch_paper_reproduction_generate as dispatch_paper_reproduction_generate_usecase,
)
from airas.usecases.reproduction.dispatch_paper_reproduction_run import (
    dispatch_paper_reproduction_run as dispatch_paper_reproduction_run_usecase,
)
from airas.usecases.reproduction.dispatch_parameter_tuning_run import (
    dispatch_parameter_tuning_run as dispatch_parameter_tuning_run_usecase,
)
from airas.usecases.reproduction.fetch_paper_reproduction_results import (
    fetch_paper_reproduction_results as fetch_paper_reproduction_results_usecase,
)
from airas.usecases.reproduction.fetch_parameter_tuning_results import (
    fetch_parameter_tuning_results as fetch_parameter_tuning_results_usecase,
)


def _config(github_owner: str, repository_name: str, branch_name: str) -> GitHubConfig:
    return GitHubConfig(
        github_owner=github_owner,
        repository_name=repository_name,
        branch_name=branch_name,
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
    return await dispatch_paper_reproduction_generate_usecase(
        _github_client(),
        _config(github_owner, repository_name, branch_name),
        paper_url,
        instruction,
        model,
        repo_url=repo_url,
        github_actions_agent=github_actions_agent,
        runner_label=runner_label,
    )


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
    return await dispatch_paper_reproduction_run_usecase(
        _github_client(),
        _config(github_owner, repository_name, branch_name),
        repro_id,
        repo_url=repo_url,
        runner_label=runner_label,
    )


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
    started = time.time()
    result = await fetch_paper_reproduction_results_usecase(
        _github_client(),
        _litellm_client(),
        _config(github_owner, repository_name, branch_name),
        repro_id,
        NodeLLMConfig(llm_name=model),
    )
    result["execution_time"] = {
        "fetch_paper_reproduction_results": [round(time.time() - started, 4)]
    }
    return result


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
    return await dispatch_parameter_tuning_run_usecase(
        _github_client(),
        _config(github_owner, repository_name, branch_name),
        repro_id,
        repo_url=repo_url,
        runner_label=runner_label,
    )


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
    return await fetch_parameter_tuning_results_usecase(
        _github_client(), _config(github_owner, repository_name, branch_name), repro_id
    )
