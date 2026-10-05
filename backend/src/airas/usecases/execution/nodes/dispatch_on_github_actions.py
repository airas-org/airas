import json
import logging
from typing import Any

from airas.core.types.github import GitHubConfig
from airas.infra.github_client import GithubClient, GithubClientFatalError

logger = logging.getLogger(__name__)

EXPERIMENT_WORKFLOW_FILE = "run_experiment.yml"


async def dispatch_on_github_actions(
    github_client: GithubClient,
    github_config: GitHubConfig,
    run_id: str,
    mode: str,
    runner_label: list[str],
    secret_names: list[str],
) -> dict[str, Any]:
    inputs = {
        "branch_name": github_config.branch_name,
        "run_id": run_id,
        "runner_label": json.dumps(runner_label),
        "mode": mode,
    }
    if secret_names:
        # 名前だけ。run の観測フック（.airas/sitecustomize.py）がこの名前の値を伏せる
        inputs["secret_names"] = ",".join(secret_names)

    logger.info(
        f"Dispatching {EXPERIMENT_WORKFLOW_FILE} for run_id={run_id} on branch "
        f"'{github_config.branch_name}' with runner_label={runner_label}"
    )

    async def dispatch(inputs: dict[str, str]) -> bool | dict:
        return await github_client.acreate_workflow_dispatch(
            github_config.github_owner,
            github_config.repository_name,
            EXPERIMENT_WORKFLOW_FILE,
            ref=github_config.branch_name,
            inputs=inputs,
            return_run_details=True,
        )

    try:
        response = await dispatch(inputs)
    except GithubClientFatalError as e:
        # secret_names 入力の無い古い template の workflow は未知の入力を 422 で拒む
        if "422" not in str(e) or "secret_names" not in inputs:
            raise
        logger.warning(
            "run_experiment.yml has no secret_names input (template older than "
            "airas-template #52); observed.json will redact by name pattern only"
        )
        response = await dispatch(
            {k: v for k, v in inputs.items() if k != "secret_names"}
        )

    details = response if isinstance(response, dict) else {}
    workflow_run_id = details.get("workflow_run_id")
    return {
        "dispatched": bool(response),
        "execution_id": str(workflow_run_id) if workflow_run_id is not None else None,
        "execution_url": details.get("html_url"),
    }
