import json
import logging
from typing import Any

from airas.core.types.github import GitHubConfig
from airas.infra.github_client import GithubClient

logger = logging.getLogger(__name__)

EXPERIMENT_WORKFLOW_FILE = "run_experiment.yml"


async def dispatch_on_github_actions(
    github_client: GithubClient,
    github_config: GitHubConfig,
    run_id: str,
    mode: str,
    runner_label: list[str],
) -> dict[str, Any]:
    inputs = {
        "branch_name": github_config.branch_name,
        "run_id": run_id,
        "runner_label": json.dumps(runner_label),
        "mode": mode,
    }
    logger.info(
        f"Dispatching {EXPERIMENT_WORKFLOW_FILE} for run_id={run_id} on branch "
        f"'{github_config.branch_name}' with runner_label={runner_label}"
    )
    response = await github_client.acreate_workflow_dispatch(
        github_config.github_owner,
        github_config.repository_name,
        EXPERIMENT_WORKFLOW_FILE,
        ref=github_config.branch_name,
        inputs=inputs,
        return_run_details=True,
    )
    details = response if isinstance(response, dict) else {}
    workflow_run_id = details.get("workflow_run_id")
    return {
        "dispatched": bool(response),
        "execution_id": str(workflow_run_id) if workflow_run_id is not None else None,
        "execution_url": details.get("html_url"),
    }
