import hashlib
import logging
from typing import Any

from pydantic import ValidationError

from airas.core.research_paths import RESULTS_DIR
from airas.core.types.github import GitHubConfig
from airas.core.types.run_provenance import (
    PROVENANCE_MANIFEST_PATH,
    ResultsDirProvenance,
    RunProvenanceManifest,
)
from airas.infra.github_client import GithubClient, GithubClientFatalError

logger = logging.getLogger(__name__)


async def _load_manifest(
    github_client: GithubClient, github_config: GitHubConfig
) -> RunProvenanceManifest:
    try:
        raw = await github_client.aget_repository_content(
            github_owner=github_config.github_owner,
            repository_name=github_config.repository_name,
            file_path=PROVENANCE_MANIFEST_PATH,
            branch_name=github_config.branch_name,
            as_="bytes",
        )
    except GithubClientFatalError as e:
        if e.status_code == 404:
            return RunProvenanceManifest()
        raise
    try:
        assert isinstance(raw, bytes)
        return RunProvenanceManifest.model_validate_json(raw)
    except (ValidationError, ValueError):
        logger.warning(
            f"Existing {PROVENANCE_MANIFEST_PATH} is unreadable; rebuilding "
            "it for the directories this import covers"
        )
        return RunProvenanceManifest()


async def commit_run_outputs(
    github_client: GithubClient,
    github_config: GitHubConfig,
    outputs: dict[str, bytes],
    provenance: ResultsDirProvenance,
    message: str,
) -> str:
    """One commit: the run's files under RESULTS_DIR and the provenance
    manifest the record gate pins its cross-check to. `provenance` is the
    declaration for every results directory the outputs touch; its `files`
    are filled in here from the bytes."""
    manifest = await _load_manifest(github_client, github_config)
    prefix = f"{RESULTS_DIR}/"
    by_dir: dict[str, dict[str, str]] = {}
    for path, content in outputs.items():
        relative = path.removeprefix(prefix)
        if "/" not in relative:
            continue  # a file directly under RESULTS_DIR has no directory
        dir_name = relative.split("/", 1)[0]
        by_dir.setdefault(dir_name, {})[path] = hashlib.sha256(content).hexdigest()
    for dir_name, files in by_dir.items():
        manifest.dirs[dir_name] = provenance.model_copy(update={"files": files})

    files_to_commit: dict[str, Any] = dict(outputs)
    files_to_commit[PROVENANCE_MANIFEST_PATH] = (
        manifest.model_dump_json(indent=2) + "\n"
    )
    return await github_client.acommit_multiple_files(
        github_owner=github_config.github_owner,
        repository_name=github_config.repository_name,
        branch_name=github_config.branch_name,
        files=files_to_commit,
        commit_message=message,
    )
