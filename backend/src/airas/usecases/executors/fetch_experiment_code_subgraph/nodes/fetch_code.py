import asyncio
import base64
import binascii
import logging
import time

from airas.core.types.experiment_code import ExperimentCode
from airas.core.types.github import GitHubConfig
from airas.infra.github_client import GithubClient

logger = logging.getLogger(__name__)

_MAX_RECURSION_DEPTH = 10


def _decode_base64_content(content: str) -> str:
    try:
        return base64.b64decode(content).decode("utf-8")
    except (binascii.Error, UnicodeDecodeError) as e:
        logger.error(f"Failed to decode base64 content: {e}")
        raise


async def _fetch_file(
    github_client: GithubClient,
    github_owner: str,
    repository_name: str,
    path: str,
    branch_name: str,
) -> str:
    try:
        resp = await github_client.aget_repository_content(
            github_owner=github_owner,
            repository_name=repository_name,
            file_path=path,
            branch_name=branch_name,
        )

        if not resp:
            logger.warning(f"Empty response for file: {path}")
            return ""

        if "content" not in resp:
            logger.warning(f"No 'content' field in response for file: {path}")
            return ""

        content = resp.get("content")
        if not isinstance(content, str):
            logger.error(
                f"Invalid content type for {path}: expected str, got {type(content).__name__}"
            )
            return ""

        return _decode_base64_content(content)

    except (binascii.Error, UnicodeDecodeError) as e:
        logger.error(f"Failed to decode content from {path}: {e}")
        return ""
    except Exception:
        logger.exception(f"Unexpected error fetching file at {path}")
        return ""


async def _fetch_directory_recursive(
    github_client: GithubClient,
    github_owner: str,
    repository_name: str,
    path: str,
    branch_name: str,
    base_path: str = "",
    max_depth: int = 10,
    current_depth: int = 0,
) -> dict[str, str]:
    files: dict[str, str] = {}

    if current_depth >= max_depth:
        logger.warning(f"Max recursion depth {max_depth} reached at {path}")
        return files

    try:
        resp = await github_client.aget_repository_content(
            github_owner=github_owner,
            repository_name=repository_name,
            file_path=path,
            branch_name=branch_name,
        )

        if not isinstance(resp, list):
            logger.warning(
                f"Expected list response for directory {path}, got {type(resp).__name__}"
            )
            return files

        tasks = []
        subdirs = []

        for item in resp:
            item_name = item.get("name", "")
            item_type = item.get("type", "")
            item_path = f"{path}/{item_name}" if path else item_name
            relative_path = f"{base_path}/{item_name}" if base_path else item_name

            if item_type == "file":
                tasks.append(
                    (
                        relative_path,
                        _fetch_file(
                            github_client,
                            github_owner,
                            repository_name,
                            item_path,
                            branch_name,
                        ),
                    )
                )
            elif item_type == "dir":
                subdirs.append((item_path, relative_path))

        # Fetch all files in current directory
        if tasks:
            results = await asyncio.gather(*[task for _, task in tasks])
            for (rel_path, _), content in zip(tasks, results, strict=True):
                if content:
                    files[rel_path] = content

        # Recursively fetch subdirectories
        for subdir_path, subdir_rel_path in subdirs:
            subdir_files = await _fetch_directory_recursive(
                github_client,
                github_owner,
                repository_name,
                subdir_path,
                branch_name,
                subdir_rel_path,
                max_depth,
                current_depth + 1,
            )
            files.update(subdir_files)

        logger.debug(f"Fetched {len(files)} files from {path}")

    except Exception:
        logger.exception(f"Failed to fetch directory {path}")

    return files


async def fetch_experiment_code(
    github_github_client: GithubClient,
    github_config: GitHubConfig,
) -> ExperimentCode:
    """
    Fetch experiment code files from GitHub repository.

    Recursively fetches:
    - src/ directory
    - config/ directory
    - pyproject.toml
    """
    github_owner = github_config.github_owner
    repository_name = github_config.repository_name
    branch_name = github_config.branch_name

    logger.info(
        f"Fetching experiment code from {github_owner}/{repository_name} (branch: {branch_name})"
    )
    start_time = time.time()

    # Fetch src/, config/, and pyproject.toml in parallel
    src_task = _fetch_directory_recursive(
        github_github_client,
        github_owner,
        repository_name,
        "src",
        branch_name,
        "src",
        _MAX_RECURSION_DEPTH,
    )
    config_task = _fetch_directory_recursive(
        github_github_client,
        github_owner,
        repository_name,
        "config",
        branch_name,
        "config",
        _MAX_RECURSION_DEPTH,
    )
    pyproject_task = _fetch_file(
        github_github_client,
        github_owner,
        repository_name,
        "pyproject.toml",
        branch_name,
    )

    src_files, config_files, pyproject_content = await asyncio.gather(
        src_task, config_task, pyproject_task
    )

    all_files = {}
    all_files.update(src_files)
    all_files.update(config_files)
    if pyproject_content:
        all_files["pyproject.toml"] = pyproject_content

    elapsed = time.time() - start_time
    total_files = len(all_files)

    logger.info(
        f"Fetched {total_files} files "
        f"(src: {len(src_files)}, config: {len(config_files)}, other: {1 if pyproject_content else 0}) "
        f"in {elapsed:.2f}s"
    )

    if src_files:
        logger.debug(f"src files ({len(src_files)}): {list(src_files.keys())}")
    else:
        logger.warning("No files found in src/ directory")

    if config_files:
        logger.debug(f"config files ({len(config_files)}): {list(config_files.keys())}")
    else:
        logger.warning("No files found in config/ directory")

    if not pyproject_content:
        logger.warning("pyproject.toml not found or empty")

    return ExperimentCode(files=all_files)
