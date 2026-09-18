import re
from typing import Any, Literal

from airas.core.types.github import GitHubConfig
from airas.core.types.run_stage import RunStage
from airas.infra.github_client import GithubClient
from airas.infra.seyval_client import SeyvalClient
from airas.usecases.execution.nodes.dispatch_on_github_actions import (
    dispatch_on_github_actions,
)
from airas.usecases.execution.nodes.dispatch_on_seyval import dispatch_on_seyval

Backend = Literal["github_actions", "seyval"]

# What the Makefile accepts for RUN_ID (it names a results directory and a
# config file): letters, digits, '_', '.' and '-', not starting with '.'.
_RUN_ID_PATTERN = re.compile(r"^[A-Za-z0-9_-][A-Za-z0-9_.-]*$")


def check_run_id(run_id: str) -> str:
    if not _RUN_ID_PATTERN.match(run_id):
        raise ValueError(
            f"run_id {run_id!r} may hold only letters, digits, '_', '.' and '-', "
            "and may not start with '.'"
        )
    return run_id


async def dispatch_experiment(
    github_config: GitHubConfig,
    run_id: str,
    *,
    backend: Backend,
    github_client: GithubClient,
    seyval_client: SeyvalClient | None = None,
    run_stage: RunStage = RunStage.SANITY,
    runner_label: list[str] | None = None,
    compute_id: str | None = None,
    compute_type: str = "gpu-a10",
    inputs_from_runs: list[str] | None = None,
    time_limit: str | None = None,
    resource_count: int | None = None,
    user_dockerfile_path: str | None = "Dockerfile",
    command_args: list[str] | None = None,
    workspace_id: str | None = None,
) -> dict[str, Any]:
    run_id = check_run_id(run_id)
    mode = run_stage.value
    match backend:
        case "github_actions":
            return await dispatch_on_github_actions(
                github_client,
                github_config,
                run_id,
                mode,
                runner_label or ["ubuntu-latest"],
            )
        case "seyval":
            if seyval_client is None:
                raise ValueError('backend="seyval" needs a seyval_client')
            return await dispatch_on_seyval(
                seyval_client,
                github_config,
                run_id,
                mode,
                compute_id=compute_id,
                compute_type=compute_type,
                inputs_from_runs=inputs_from_runs,
                time_limit=time_limit,
                resource_count=resource_count,
                user_dockerfile_path=user_dockerfile_path,
                command_args=command_args,
                workspace_id=workspace_id,
            )
        case _:
            raise ValueError(f"unknown backend {backend!r}")
