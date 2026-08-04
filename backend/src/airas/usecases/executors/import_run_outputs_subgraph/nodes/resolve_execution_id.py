import logging

from airas.core.types.github import GitHubConfig
from airas.infra.aixs_client import AixsClient
from airas.usecases.executors.dispatch_experiment_on_aixs_subgraph.dispatch_experiment_on_aixs_subgraph import (
    aixs_experiment_id,
)

logger = logging.getLogger(__name__)

COMPLETED_STATUS = "completed"


async def resolve_execution_id(
    aixs_client: AixsClient,
    github_config: GitHubConfig,
    run_id: str,
    mode: str,
) -> str:
    """Find the AIXS run that produced `run_id`'s outputs in `mode`.

    Dispatch names each run with an `experiment_id` derived from the run id
    and mode, so the run is found by matching that name among the
    repository's completed runs and taking the newest — re-dispatching
    reuses the name, and only the latest attempt's outputs are wanted.

    AIXS caps the listing, so a run that has aged out cannot be found this
    way and has to be addressed by its id directly.
    """
    git_url = (
        f"https://github.com/{github_config.github_owner}/"
        f"{github_config.repository_name}"
    )
    # Registration is idempotent; this is how dispatch resolves the id too.
    repository = await aixs_client.aregister_repository(git_url)
    repository_id = repository["id"]

    experiment_id = aixs_experiment_id(run_id, mode)
    runs = await aixs_client.alist_runs(repository_id)
    # The listing is newest-first, so the first match is the latest attempt.
    run = next(
        (
            r
            for r in runs
            if r.get("experiment_id") == experiment_id
            and r.get("status") == COMPLETED_STATUS
        ),
        None,
    )
    if run is not None:
        execution_id = str(run["run_id"])
        logger.info(
            f"Resolved run_id={run_id} (mode={mode}) to AIXS run {execution_id}"
        )
        return execution_id

    raise ValueError(
        f"No completed AIXS run found for run_id='{run_id}' (mode={mode}, "
        f"experiment_id='{experiment_id}') in {git_url}. The run may still be "
        "in progress, may have failed, or may have aged out of the listing "
        f"({len(runs)} runs listed). Pass execution_id explicitly to import a "
        "specific run."
    )
