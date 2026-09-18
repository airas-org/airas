from typing import Any

from airas.core.types.github import GitHubConfig
from airas.infra.github_client import GithubClient
from airas.usecases.reproduction.nodes.dispatch_reproduction_workflow import (
    dispatch_reproduction_workflow,
)
from airas.usecases.reproduction.nodes.validate_repro_id import validate_repro_id

WORKFLOW_FILE = "run_parameter_tuning_run.yml"


async def dispatch_parameter_tuning_run(
    github_client: GithubClient,
    github_config: GitHubConfig,
    repro_id: str,
    *,
    repo_url: str = "",
    runner_label: list[str] | None = None,
    workflow_file: str = WORKFLOW_FILE,
) -> dict[str, Any]:
    """No code generation: tune_driver.py reuses the reproduction's src/main.py."""
    dispatched = await dispatch_reproduction_workflow(
        github_client,
        github_config,
        workflow_file,
        {"repro_id": validate_repro_id(repro_id), "repo_url": repo_url},
        runner_label,
    )
    return {"dispatched": dispatched}
