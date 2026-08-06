import asyncio
import base64
import json
import logging
from typing import Any

from airas.core.research_paths import DIAGRAM_DIR, LEGACY_DIAGRAM_DIR, RESULTS_DIR
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
    github_client: GithubClient,
    github_owner: str,
    repository_name: str,
    file_path: str,
    branch_name: str,
) -> dict[str, Any] | None:
    try:
        resp = await github_client.aget_repository_content(
            github_owner=github_owner,
            repository_name=repository_name,
            file_path=file_path,
            branch_name=branch_name,
        )
        if resp and "content" in resp:
            content_str = _decode_base64_content(resp["content"])
            return json.loads(content_str)
    except (json.JSONDecodeError, Exception) as e:
        logger.error(f"Failed to fetch or parse JSON at {file_path}: {e}")
    return None


# Figures are collected into the paper's images/ directory with their
# directory structure preserved (see collect_latex_project_files), so a run
# that writes chart/loss.pdf is referenced as images/chart/loss.pdf. Listing
# bare filenames here would make two runs' loss.pdf indistinguishable and
# would point the paper at images/loss.pdf, which nothing creates.
MAX_LISTING_DEPTH = 4

# Only PDFs count as figures. Both collectors (`_merge_figure` and the
# template's compile_latex.yml rsync) copy `*.pdf` and nothing else, so
# anything else listed here would send the paper after an image that never
# lands under images/ — and a run writes checkpoints, logs and raw
# artifacts into its results directory alongside the figures.
FIGURE_SUFFIX = ".pdf"


async def _fetch_figure_paths(
    github_client: GithubClient,
    github_owner: str,
    repository_name: str,
    dir_path: str,
    branch_name: str,
    _depth: int = 0,
) -> list[str]:
    """List figure PDFs under `dir_path`, recursively, relative to it."""
    try:
        resp = await github_client.aget_repository_content(
            github_owner=github_owner,
            repository_name=repository_name,
            file_path=dir_path,
            branch_name=branch_name,
        )
    except Exception as e:
        logger.error(f"Failed to list files in {dir_path}: {e}")
        return []

    if not isinstance(resp, list):
        return []

    files = [
        entry["name"]
        for entry in resp
        if entry.get("type") == "file"
        and str(entry.get("name", "")).lower().endswith(FIGURE_SUFFIX)
    ]

    subdirs = [entry["name"] for entry in resp if entry.get("type") == "dir"]
    if not subdirs:
        return files

    if _depth >= MAX_LISTING_DEPTH:
        logger.warning(
            f"Stopped descending at {dir_path}: depth limit "
            f"{MAX_LISTING_DEPTH} reached, skipping {len(subdirs)} subdirectories"
        )
        return files

    nested = await asyncio.gather(
        *(
            _fetch_figure_paths(
                github_client,
                github_owner,
                repository_name,
                f"{dir_path}/{subdir}",
                branch_name,
                _depth=_depth + 1,
            )
            for subdir in subdirs
        )
    )
    for subdir, subdir_files in zip(subdirs, nested, strict=True):
        files.extend(f"{subdir}/{name}" for name in subdir_files)
    return files


async def _process_run_data(
    github_client: GithubClient,
    github_config: GitHubConfig,
    run_id: str,
    results_dir: str,
) -> tuple[str, dict[str, Any] | None, list[str]]:
    run_dir = f"{results_dir}/{run_id}"
    metrics_path = f"{run_dir}/metrics.json"

    metrics_task = _fetch_json(
        github_client,
        github_config.github_owner,
        github_config.repository_name,
        metrics_path,
        github_config.branch_name,
    )
    files_task = _fetch_figure_paths(
        github_client,
        github_config.github_owner,
        github_config.repository_name,
        run_dir,
        github_config.branch_name,
    )

    metrics, files = await asyncio.gather(metrics_task, files_task)

    if metrics:
        logger.info(f"Retrieved metrics for run {run_id}")
    if files:
        logger.info(f"Retrieved {len(files)} figures for run {run_id}")

    # Relative to results_dir, which is what the paper references under images/.
    return run_id, metrics, [f"{run_id}/{name}" for name in files]


async def _process_comparison_data(
    github_client: GithubClient,
    github_config: GitHubConfig,
    results_dir: str,
) -> tuple[dict[str, Any] | None, list[str]]:
    comp_dir = f"{results_dir}/comparison"
    agg_path = f"{comp_dir}/aggregated_metrics.json"

    metrics_task = _fetch_json(
        github_client,
        github_config.github_owner,
        github_config.repository_name,
        agg_path,
        github_config.branch_name,
    )
    files_task = _fetch_figure_paths(
        github_client,
        github_config.github_owner,
        github_config.repository_name,
        comp_dir,
        github_config.branch_name,
    )

    metrics, files = await asyncio.gather(metrics_task, files_task)

    if metrics:
        logger.info("Retrieved aggregated metrics")
    if files:
        logger.info(f"Retrieved {len(files)} comparison files")

    return metrics, [f"comparison/{name}" for name in files]


def _image_prefix(dir_path: str, results_dir: str) -> str:
    """The path `dir_path`'s contents take under the paper's images/.

    Directories inside `results_dir` keep the part below it; the legacy
    diagram directory sits outside and is merged into images/ flat, which is
    what collect_latex_project_files does with each of these roots.
    """
    if dir_path == results_dir:
        return ""
    if dir_path.startswith(f"{results_dir}/"):
        return f"{dir_path[len(results_dir) + 1 :]}/"
    return ""


async def _fetch_diagram_files(
    github_client: GithubClient,
    github_config: GitHubConfig,
    results_dir: str = RESULTS_DIR,
    diagrams_dirs: tuple[str, ...] = (DIAGRAM_DIR, LEGACY_DIAGRAM_DIR),
) -> list[str]:
    per_dir = await asyncio.gather(
        *(
            _fetch_figure_paths(
                github_client,
                github_config.github_owner,
                github_config.repository_name,
                diagrams_dir,
                github_config.branch_name,
            )
            for diagrams_dir in diagrams_dirs
        )
    )
    files = [
        f"{_image_prefix(diagrams_dir, results_dir)}{name}"
        for diagrams_dir, dir_files in zip(diagrams_dirs, per_dir, strict=True)
        for name in dir_files
    ]
    if files:
        logger.info(
            f"Retrieved {len(files)} diagram files from {', '.join(diagrams_dirs)}"
        )
    return files


async def fetch_results(
    github_client: GithubClient,
    github_config: GitHubConfig,
    run_ids: list[str],
    results_dir: str = RESULTS_DIR,
) -> ExperimentalResults:
    if not run_ids:
        raise ValueError("run_ids must not be empty")

    logger.info(f"Retrieving results for {len(run_ids)} runs from {results_dir}")

    tasks = [
        _process_run_data(github_client, github_config, run_id, results_dir)
        for run_id in run_ids
    ]
    comp_task = _process_comparison_data(github_client, github_config, results_dir)
    diagrams_task = _fetch_diagram_files(github_client, github_config, results_dir)

    run_results_list, (comp_metrics, comp_files), diagram_files = await asyncio.gather(
        asyncio.gather(*tasks), comp_task, diagrams_task
    )

    final_metrics: dict[str, Any] = {}
    result_figures: list[str] = []

    for r_id, r_metrics, r_files in run_results_list:
        if r_metrics:
            final_metrics[r_id] = r_metrics
        if r_files:
            result_figures.extend(r_files)

    if comp_metrics:
        final_metrics["comparison"] = comp_metrics
    if comp_files:
        result_figures.extend(comp_files)

    logger.info(
        f"Combined results: {len(final_metrics)} metrics entries, "
        f"{len(result_figures)} result figures, {len(diagram_files)} diagram figures"
    )

    return ExperimentalResults(
        metrics_data=final_metrics if final_metrics else None,
        result_figures=result_figures if result_figures else None,
        diagram_figures=diagram_files if diagram_files else None,
    )
