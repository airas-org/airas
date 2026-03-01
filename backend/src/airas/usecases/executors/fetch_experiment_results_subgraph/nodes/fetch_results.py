import asyncio
import base64
import json
import logging
from typing import Any

from airas.core.types.experimental_results import ExperimentalResults
from airas.core.types.github import GitHubConfig
from airas.infra.github_client import GithubClient

logger = logging.getLogger(__name__)


def _decode_base64_content(content: str) -> str:
    try:
        return base64.b64decode(content).decode("utf-8")
    except Exception as e:
        logger.error(f"Failed to decode base64 content: {e}")
        raise


async def _fetch_json(
    client: GithubClient,
    owner: str,
    repo: str,
    path: str,
    branch: str,
) -> dict[str, Any] | None:
    try:
        resp = await client.aget_repository_content(
            github_owner=owner,
            repository_name=repo,
            file_path=path,
            branch_name=branch,
        )
        if resp and "content" in resp:
            content_str = _decode_base64_content(resp["content"])
            return json.loads(content_str)
    except (json.JSONDecodeError, Exception) as e:
        logger.error(f"Failed to fetch or parse JSON at {path}: {e}")
    return None


async def _fetch_file_paths(
    client: GithubClient,
    owner: str,
    repo: str,
    dir_path: str,
    branch: str,
    exclude_names: set[str] | None = None,
) -> list[str]:
    try:
        resp = await client.aget_repository_content(
            github_owner=owner,
            repository_name=repo,
            file_path=dir_path,
            branch_name=branch,
        )
        if isinstance(resp, list):
            excludes = exclude_names or set()
            return [
                f["name"]
                for f in resp
                if f.get("type") == "file" and f.get("name") not in excludes
            ]
    except Exception as e:
        logger.error(f"Failed to list files in {dir_path}: {e}")
    return []


async def _process_run_data(
    client: GithubClient,
    config: GitHubConfig,
    run_id: str,
    results_dir: str,
) -> tuple[str, dict[str, Any] | None, list[str]]:
    run_dir = f"{results_dir}/{run_id}"
    metrics_path = f"{run_dir}/metrics.json"

    metrics_task = _fetch_json(
        client,
        config.github_owner,
        config.repository_name,
        metrics_path,
        config.branch_name,
    )
    files_task = _fetch_file_paths(
        client,
        config.github_owner,
        config.repository_name,
        run_dir,
        config.branch_name,
        exclude_names={"metrics.json"},
    )

    metrics, files = await asyncio.gather(metrics_task, files_task)

    if metrics:
        logger.info(f"Retrieved metrics for run {run_id}")
    if files:
        logger.info(f"Retrieved {len(files)} figures for run {run_id}")

    return run_id, metrics, files


async def _process_comparison_data(
    client: GithubClient,
    config: GitHubConfig,
    results_dir: str,
) -> tuple[dict[str, Any] | None, list[str]]:
    comp_dir = f"{results_dir}/comparison"
    agg_path = f"{comp_dir}/aggregated_metrics.json"

    metrics_task = _fetch_json(
        client,
        config.github_owner,
        config.repository_name,
        agg_path,
        config.branch_name,
    )
    files_task = _fetch_file_paths(
        client,
        config.github_owner,
        config.repository_name,
        comp_dir,
        config.branch_name,
        exclude_names={"aggregated_metrics.json"},
    )

    metrics, files = await asyncio.gather(metrics_task, files_task)

    if metrics:
        logger.info("Retrieved aggregated metrics")
    if files:
        logger.info(f"Retrieved {len(files)} comparison files")

    return metrics, files


async def _fetch_diagram_files(
    client: GithubClient,
    config: GitHubConfig,
    diagrams_dir: str = ".research/diagrams",
) -> list[str]:
    files = await _fetch_file_paths(
        client,
        config.github_owner,
        config.repository_name,
        diagrams_dir,
        config.branch_name,
    )
    if files:
        logger.info(f"Retrieved {len(files)} diagram files from {diagrams_dir}")
    return [f"{diagrams_dir}/{f}" for f in files]


async def fetch_results(
    github_client: GithubClient,
    github_config: GitHubConfig,
    run_ids: list[str],
    results_dir: str = ".research/results",
) -> ExperimentalResults:
    if not run_ids:
        logger.warning("No run_ids provided")
        return ExperimentalResults()

    logger.info(f"Retrieving results for {len(run_ids)} runs from {results_dir}")

    tasks = [
        _process_run_data(github_client, github_config, run_id, results_dir)
        for run_id in run_ids
    ]
    comp_task = _process_comparison_data(github_client, github_config, results_dir)
    diagrams_task = _fetch_diagram_files(github_client, github_config)

    run_results_list, (comp_metrics, comp_files), diagram_files = await asyncio.gather(
        asyncio.gather(*tasks), comp_task, diagrams_task
    )

    final_metrics: dict[str, Any] = {}
    final_figures: list[str] = []

    for r_id, r_metrics, r_files in run_results_list:
        if r_metrics:
            final_metrics[r_id] = r_metrics
        if r_files:
            final_figures.extend(r_files)

    if comp_metrics:
        final_metrics["comparison"] = comp_metrics
    if comp_files:
        final_figures.extend(comp_files)
    if diagram_files:
        final_figures.extend(diagram_files)

    logger.info(
        f"Combined results: {len(final_metrics)} metrics entries, {len(final_figures)} figures"
    )

    return ExperimentalResults(
        metrics_data=final_metrics if final_metrics else None,
        figures=final_figures if final_figures else None,
    )
