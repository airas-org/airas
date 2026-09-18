import logging
from typing import Any

from airas.core.research_paths import RESULTS_DIR
from airas.core.types.github import GitHubConfig
from airas.core.types.run_provenance import ResultsDirProvenance
from airas.core.types.run_stage import RunStage
from airas.infra.github_client import GithubClient
from airas.infra.run_output_store import RunOutputStore
from airas.usecases.execution.nodes.collect_run_outputs import collect_run_outputs
from airas.usecases.execution.nodes.commit_run_outputs import commit_run_outputs

logger = logging.getLogger(__name__)


async def import_run_outputs(
    github_config: GitHubConfig,
    run_id: str,
    *,
    store: RunOutputStore,
    github_client: GithubClient,
    execution_id: str,
    run_stage: RunStage = RunStage.FULL,
) -> dict[str, Any]:
    """Copy a finished run's files from the backend's store into the
    repository, with the provenance manifest, in one commit."""
    outputs = await collect_run_outputs(store, execution_id)

    # Best effort: verification re-fetches the run from the backend, so a
    # failed metadata fetch must not fail an import whose outputs downloaded.
    commit_hash: str | None = None
    overrides: dict[str, str] = {}
    parameters: dict[str, str] = {}
    try:
        run = next(
            r for r in await store.alist_runs() if r.execution_id == execution_id
        )
        commit_hash, overrides, parameters = (
            run.commit_hash,
            run.overrides or {},
            run.parameters or {},
        )
    except Exception as e:
        logger.warning(
            f"Could not fetch run metadata for {execution_id}; the manifest "
            f"will omit its commit hash and parameters: {e}"
        )

    import_commit_sha = await commit_run_outputs(
        github_client,
        github_config,
        outputs,
        ResultsDirProvenance(
            execution_id=execution_id,
            backend=store.backend,
            commit_hash=commit_hash,
            overrides=overrides,
            parameters=parameters,
            files={},
        ),
        f"Import {store.backend} run outputs for {run_id} ({run_stage.value}) "
        f"from run {execution_id}",
    )
    paths = sorted(outputs)
    total_bytes = sum(len(c) for c in outputs.values())
    logger.info(
        f"Imported {len(paths)} files ({total_bytes} bytes) into {RESULTS_DIR}/ "
        f"on branch '{github_config.branch_name}' as commit {import_commit_sha[:12]}"
    )
    return {
        "imported": bool(import_commit_sha),
        "execution_id": execution_id,
        "imported_paths": paths,
        "total_bytes": total_bytes,
        "import_commit_sha": import_commit_sha,
    }
