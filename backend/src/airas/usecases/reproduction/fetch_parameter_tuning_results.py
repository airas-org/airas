import logging
from typing import Any

from airas.core.types.github import GitHubConfig
from airas.infra.github_client import GithubClient
from airas.usecases.reproduction.nodes.fetch_tuning_outputs import fetch_tuning_outputs
from airas.usecases.reproduction.nodes.validate_repro_id import validate_repro_id

logger = logging.getLogger(__name__)


async def fetch_parameter_tuning_results(
    github_client: GithubClient, github_config: GitHubConfig, repro_id: str
) -> dict[str, Any]:
    validate_repro_id(repro_id)
    try:
        outputs = await fetch_tuning_outputs(
            github_client=github_client, github_config=github_config, repro_id=repro_id
        )
    except Exception as exc:
        logger.exception("Failed to fetch tuning outputs")
        return {
            "result": None,
            "tuning_figure_png_base64": None,
            "final_status": {"status": "failed", "fetch_error": str(exc)},
        }
    result = outputs.get("result")
    figure = outputs.get("tuning_figure_png_base64")
    if not isinstance(result, dict):
        status = {"status": "failed", "run_error": "result_missing"}
        result = None
    elif result.get("error"):
        status = {"status": "failed", "run_error": result["error"]}
    else:
        status = {"status": "passed"}
    return {
        "result": result,
        "tuning_figure_png_base64": figure,
        "final_status": status,
    }
