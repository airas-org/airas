import logging
from datetime import datetime, timezone
from typing import Any

from airas.utils.api_client.github_client import GithubClient

logger = logging.getLogger(__name__)


def _dict_conflict(old: Any, new: Any) -> bool:
    if isinstance(old, dict) and isinstance(new, dict):
        for key in old.keys() & new.keys():
            if _dict_conflict(old[key], new[key]):
                return True
        return False
    return old != new


def prepare_branch(
    github_owner: str,
    repository_name: str,
    branch_name: str,
    research_history: dict[str, Any],
    new_output: dict[str, Any],
    subgraph_name: str | None, 
    client: GithubClient | None = None,
) -> str:
    if client is None:
        client = GithubClient()

    if not _dict_conflict(research_history, new_output):
        logger.info(f"No overwrite conflict – keeping branch '{branch_name}'")
        return branch_name

    base_info = client.get_branch(
        github_owner, repository_name, branch_name
    )
    if base_info is None:
        raise RuntimeError(
            f"Branch '{branch_name}' not found in {github_owner}/{repository_name}"
        )

    sha = base_info["commit"]["sha"]
    ts = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    new_branch = f"{branch_name}-{subgraph_name}-{ts}"

    client.create_branch(
        github_owner, repository_name, new_branch, from_sha=sha
    )
    logger.info(f"Conflict detected – created branch '{new_branch}' from '{branch_name}'")
    return new_branch