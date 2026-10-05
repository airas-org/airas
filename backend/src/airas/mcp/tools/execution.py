"""Experiment execution: dispatch a run, follow it, bring its outputs back."""

import asyncio
import logging
import os
from typing import Any, Literal

from airas.core.types.execution_backend import ExecutionBackend
from airas.core.types.github import GitHubConfig
from airas.core.types.run_stage import RunStage
from airas.infra.github.nodes.download_artifact import download_and_parse_artifact
from airas.mcp.app import mcp
from airas.mcp.context import (
    _github_client,
    _output_store,
    _seyval_client,
)
from airas.usecases.execution.cancel_experiment import (
    cancel_experiment as cancel_experiment_usecase,
)
from airas.usecases.execution.dispatch_experiment import (
    dispatch_experiment as dispatch_experiment_usecase,
)
from airas.usecases.execution.fetch_experiment_results import (
    fetch_experiment_results as fetch_experiment_results_usecase,
)
from airas.usecases.execution.get_experiment_run_status import (
    get_experiment_run_status as get_experiment_run_status_usecase,
)
from airas.usecases.execution.import_run_outputs import (
    import_run_outputs as import_run_outputs_usecase,
)

logger = logging.getLogger(__name__)


@mcp.tool()
async def dispatch_experiment(
    github_owner: str,
    repository_name: str,
    branch_name: str,
    run_id: str,
    run_stage: Literal["sanity", "pilot", "full"] = "sanity",
    runner_label: list[str] | None = None,
    backend: ExecutionBackend = "github_actions",
    compute_type: str = "gpu-a10",
    compute_id: str | None = None,
    inputs_from_runs: list[str] | None = None,
    time_limit: str | None = None,
    resource_count: int | None = None,
    user_dockerfile_path: str | None = "Dockerfile",
    command_args: list[str] | None = None,
    workspace_id: str | None = None,
) -> dict[str, Any]:
    """Start an experiment run (asynchronous). The code must already be pushed.

    `run_stage` selects the stage, in increasing scale: "sanity" for a quick
    correctness run, "pilot" for a small preliminary one, "full" for the real
    experiment. `run_id` identifies the experiment run defined by the
    experiment code (one config/run/{run_id}.yaml). Pass the same stage to
    `import_run_outputs` to collect the run's results afterwards.

    `backend` selects where the run executes; either way the run's outputs
    stay on the backend's side until `import_run_outputs` copies them into
    the repository with their provenance, and the returned `execution_id` is
    what that call and `get_experiment_run_status` take. Either way the run
    receives the *names* of the secrets registered in
    `~/.airas/credentials.json` as `AIRAS_SECRET_NAMES` (the workflow input
    `secret_names` on GitHub Actions, an `env` prefix of the command on
    Seyval): the repository's observation hook redacts those values from
    `observed.json`. The values themselves come from the backend's own
    secret store.
    - "github_actions" (default): dispatches run_experiment.yml in the
      experiment repository; `runner_label` picks the runner. Requires
      GH_PERSONAL_ACCESS_TOKEN.
    - "seyval": executes on the Seyval compute platform. `compute_id` picks
      the machine — normally a cluster you registered, "byo:<uuid>" from the
      Seyval MCP server's `list_computes`; it defaults to SEYVAL_COMPUTE_ID,
      and without either the run goes to Seyval-managed compute.
      `compute_type` sets the resource request in both cases (e.g.
      "cpu-general", "gpu-a10"). `workspace_id` (default SEYVAL_WORKSPACE_ID)
      is required when your key sees several workspaces: a repository is
      registered into one for good.

    `user_dockerfile_path` (default "Dockerfile") makes Seyval build the
    committed Dockerfile as-is instead of generating an environment; pass
    None to let it generate one. Its CMD then runs verbatim, so the run's
    command is `command_args` (argv), which defaults to
    `make run RUN_ID=<run_id> MODE=<run_stage>` — the repository's one entry
    point, the same one run_experiment.yml calls. The Makefile reads the
    run's kind from `config/run/<run_id>.yaml`: an experiment runs
    `src.main`, airas-eval and `src.evaluate` (a run that stops after
    `src.main` writes no metrics.json and fails verification); a `lean` run
    builds the module and writes `lean.json`. Lean has sanity and full
    stages only.

    `inputs_from_runs`, `time_limit` and `resource_count` apply to "seyval"
    only. `inputs_from_runs` takes `execution_id`s of earlier completed runs
    and restores their outputs into this run's working directory at the paths
    they were written to, so a run can consume what a previous one produced.
    `time_limit` (e.g. "24:00:00") and `resource_count` request per-run
    resources from a registered cluster; accepted values are in its
    `run_profile` from `list_computes`.
    """
    stage = RunStage(run_stage)
    seyval_client = None
    resolved_compute_id = None
    if backend == "seyval":
        # Resolve the client first: it is what loads the stored credentials
        # into the environment that SEYVAL_COMPUTE_ID is read from.
        seyval_client = _seyval_client()
        resolved_compute_id = compute_id or os.getenv("SEYVAL_COMPUTE_ID") or None

    result = await dispatch_experiment_usecase(
        GitHubConfig(
            github_owner=github_owner,
            repository_name=repository_name,
            branch_name=branch_name,
        ),
        run_id,
        backend=backend,
        github_client=_github_client(),
        seyval_client=seyval_client,
        run_stage=stage,
        runner_label=runner_label,
        compute_id=resolved_compute_id,
        compute_type=compute_type,
        inputs_from_runs=inputs_from_runs,
        time_limit=time_limit,
        resource_count=resource_count,
        user_dockerfile_path=user_dockerfile_path,
        command_args=command_args,
        workspace_id=workspace_id or os.getenv("SEYVAL_WORKSPACE_ID") or None,
    )
    return {**result, "backend": backend, "compute_id": resolved_compute_id}


@mcp.tool()
async def get_experiment_run_status(
    execution_id: str,
    backend: ExecutionBackend = "github_actions",
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
    return await get_experiment_run_status_usecase(
        execution_id,
        backend=backend,
        github_client=_github_client() if backend == "github_actions" else None,
        seyval_client=_seyval_client() if backend == "seyval" else None,
        github_owner=github_owner,
        repository_name=repository_name,
        log_tail_lines=log_tail_lines,
    )


@mcp.tool()
async def cancel_experiment(
    execution_id: str,
    backend: ExecutionBackend = "github_actions",
    github_owner: str | None = None,
    repository_name: str | None = None,
) -> dict[str, Any]:
    """Cancel a running experiment (asynchronous, irreversible).

    `execution_id` identifies the run on the selected `backend`, exactly as
    for `get_experiment_run_status`: the `execution_id` returned by
    `dispatch_experiment(backend="seyval")`, or a `workflow_run_id` from
    `get_workflow_runs` for "github_actions" (pass `github_owner` and
    `repository_name` in that case).

    The cancel is only requested here; the run winds down on the backend's
    side, so poll `get_experiment_run_status` until it reports "cancelled".
    `cancelled` is False when the run had already finished, in which case
    nothing changes. Outputs written before the cancel stay on the backend
    and `import_run_outputs` can still collect them.
    """
    return await cancel_experiment_usecase(
        execution_id,
        backend=backend,
        github_client=_github_client() if backend == "github_actions" else None,
        seyval_client=_seyval_client() if backend == "seyval" else None,
        github_owner=github_owner,
        repository_name=repository_name,
    )


@mcp.tool()
async def get_workflow_runs(
    github_owner: str,
    repository_name: str,
    branch_name: str | None = None,
    limit: int = 5,
    event: str | None = None,
) -> list[dict[str, Any]]:
    """Check the status of recent GitHub Actions runs in the experiment repository (non-blocking).

    Returns the most recent workflow runs with their status, conclusion and
    the commit they ran on, newest first. Runs from every trigger are
    included, so this is also how the record gate (`Verify Record`, which
    runs on push) and `Publish Paper` are read: pass `branch_name="verify"`
    to follow the staging ref, and match `head_sha` against the sha you
    pushed. Pass `event="workflow_dispatch"` to see only runs started by
    `dispatch_experiment`. Poll it between other work instead of waiting.
    Requires GH_PERSONAL_ACCESS_TOKEN.
    """
    response = await _github_client().alist_workflow_runs(
        github_owner=github_owner,
        repository_name=repository_name,
        branch_name=branch_name,
        event=event,
    )
    runs = (response or {}).get("workflow_runs", [])[:limit]
    return [
        {
            "workflow_run_id": run.get("id"),
            "name": run.get("name"),
            "event": run.get("event"),
            "head_branch": run.get("head_branch"),
            "head_sha": run.get("head_sha"),
            "status": run.get("status"),
            "conclusion": run.get("conclusion"),
            "created_at": run.get("created_at"),
            "html_url": run.get("html_url"),
        }
        for run in runs
    ]


@mcp.tool()
async def fetch_experiment_results(local_path: str) -> dict[str, Any]:
    """Read what the runs left under `.research/results/` in the clone.

    Use after `import_run_outputs` has committed a run's outputs and the
    clone has pulled them. Returns, per results directory, the `metrics`
    (metrics.json), the airas-eval `evaluation` report (metrics, curves,
    skipped metrics with reasons), the `figures` under it, and the entry
    the provenance manifest holds for it (None when the directory arrived
    some other way, which `verify_record` will fail). Nothing is
    interpreted here: the record's verdicts come from `update_record`.
    """
    return await asyncio.to_thread(fetch_experiment_results_usecase, local_path)


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
    execution_id: str,
    run_stage: Literal["sanity", "pilot", "full", "visualization"] = "full",
    backend: ExecutionBackend = "github_actions",
    confirm_overwrite: bool = False,
) -> dict[str, Any]:
    """Copy a finished run's result files from the backend's store into the repository.

    Neither backend pushes results back: Seyval keeps them in its storage and
    a GitHub Actions run uploads them as a workflow artifact. This downloads
    everything the run wrote under `.research/results/` and commits it to
    `branch_name` at the same paths, together with
    `.research/results/.provenance.json` declaring, per results directory,
    the backend, `execution_id`, commit, dispatch parameters and each file's
    sha256. `verify_record` pins its cross-check to that declaration, so
    results that arrive any other way, or are edited afterwards, fail.

    `execution_id` is what `dispatch_experiment` returned and `backend` the
    one it ran on. Call it once `get_experiment_run_status` reports a
    terminal status.

    A repository path holds one run's results regardless of stage, so
    importing a provisional stage ("sanity" or "pilot") replaces the full
    run's results at the paths they share, and requires
    `confirm_overwrite=True`. "visualization" needs no confirmation because
    such a run adds figures derived from an earlier run.

    File contents never leave airas. Requires GH_PERSONAL_ACCESS_TOKEN, and
    SEYVAL_API_KEY for `backend="seyval"`.
    """
    stage = RunStage(run_stage)
    if stage in _PROVISIONAL_RUN_STAGES and not confirm_overwrite:
        raise ValueError(
            f"A {stage.value} run re-runs the experiment and writes the same "
            f"file names as the full run of '{run_id}', so importing it would "
            "replace the full run's results at those paths. Pass "
            "confirm_overwrite=True to do it anyway."
        )

    return await import_run_outputs_usecase(
        GitHubConfig(
            github_owner=github_owner,
            repository_name=repository_name,
            branch_name=branch_name,
        ),
        run_id,
        store=_output_store(
            backend, f"https://github.com/{github_owner}/{repository_name}"
        ),
        github_client=_github_client(),
        execution_id=execution_id,
        run_stage=stage,
    )


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
    return await download_and_parse_artifact(
        github_client=_github_client(),
        github_config=GitHubConfig(
            github_owner=github_owner,
            repository_name=repository_name,
            branch_name=branch_name,
        ),
        workflow_run_id=workflow_run_id,
    )
