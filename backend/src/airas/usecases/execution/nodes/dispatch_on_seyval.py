import logging
import shlex
from typing import Any

from airas.core.types.github import GitHubConfig
from airas.infra.seyval_client import SeyvalClient

logger = logging.getLogger(__name__)

RUN_COMMAND_TEMPLATE = "make run RUN_ID={run_id} MODE={mode}"
_ANALYSIS_ACTIVE = ("pending", "running")


def run_command(run_id: str, mode: str) -> str:
    return RUN_COMMAND_TEMPLATE.format(
        run_id=shlex.quote(run_id), mode=shlex.quote(mode)
    )


async def _analyzed(
    client: SeyvalClient, repository_id: str, commit_hash: str, branch: str
) -> tuple[str, str]:
    try:
        analysis = await client.aget_analysis(repository_id, commit_hash)
    except Exception:
        await client.astart_analysis(repository_id, commit_hash, branch=branch)
        analysis = await client.aget_analysis(repository_id, commit_hash)
    status = analysis.get("status")
    if status in _ANALYSIS_ACTIVE:
        raise ValueError(
            f"Seyval is still analyzing commit {commit_hash[:12]} "
            f"(status: {status}); it takes a few minutes — call "
            "dispatch_experiment again once it is completed."
        )
    experiments = analysis.get("experiments") or []
    if status != "completed" or not experiments:
        raise ValueError(
            f"Seyval's analysis of commit {commit_hash[:12]} ended with "
            f"status {status!r} and {len(experiments)} experiment(s): "
            f"{analysis.get('error') or 'no runnable experiment found'}"
        )
    primary = (analysis.get("primary_ids") or [None])[0]
    experiment_id = primary or experiments[0]["id"]
    return str(analysis["analysis_id"]), str(experiment_id)


async def dispatch_on_seyval(
    client: SeyvalClient,
    github_config: GitHubConfig,
    run_id: str,
    mode: str,
    *,
    compute_id: str | None,
    compute_type: str,
    inputs_from_runs: list[str] | None,
    time_limit: str | None,
    resource_count: int | None,
    user_dockerfile_path: str | None,
    command_args: list[str] | None,
    workspace_id: str | None,
) -> dict[str, Any]:
    git_url = f"https://github.com/{github_config.github_owner}/{github_config.repository_name}"
    repository = await client.aregister_repository(git_url, workspace_id=workspace_id)
    repository_id = repository["id"]

    pulled = await client.apull_repository(repository_id)
    branch = next(
        (
            b
            for b in pulled.get("branches", [])
            if b.get("name") == github_config.branch_name
        ),
        None,
    )
    if branch is None:
        raise ValueError(
            f"Branch '{github_config.branch_name}' not found in {git_url}. "
            "Push the experiment code before dispatching."
        )
    commit_hash = branch["commit_hash"]
    analysis_id, experiment_id = await _analyzed(
        client, repository_id, commit_hash, github_config.branch_name
    )
    logger.info(
        f"Starting Seyval run for run_id={run_id} (mode={mode}, "
        f"compute_id={compute_id}, compute_type={compute_type}) at commit {commit_hash[:12]}"
    )
    run = await client.astart_run(
        repository_id,
        commit_hash,
        experiment_id,
        analysis_id,
        compute_type=compute_type,
        compute_id=compute_id,
        inputs_from_runs=inputs_from_runs,
        time_limit=time_limit,
        resource_count=resource_count,
        user_dockerfile_path=user_dockerfile_path,
        command_args=command_args or ["bash", "-c", run_command(run_id, mode)],
    )
    return {
        "dispatched": True,
        "execution_id": str(run["run_id"]),
        "execution_url": run.get("run_url") or None,
    }
