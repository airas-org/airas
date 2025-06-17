import argparse
import logging
from copy import deepcopy
from typing import Any

from airas.core.github.nodes.github_download import github_download
from airas.core.github.nodes.github_upload import github_upload
from airas.services.api_client.github_client import GithubClient

logger = logging.getLogger(__name__)


def _prune_history(history: dict[str, Any], restart_from: str) -> dict[str, Any]:
    if not history:
        raise ValueError(" is empty or does not exist.")

    history = deepcopy(history)
    order = history.get("_order", [])
    if restart_from not in order:
        raise ValueError(f"{restart_from} is not found in _order.")

    keep_until = order.index(restart_from)
    keep_set = set(order[:keep_until])

    history["_order"] = order[:keep_until]

    for key in list(history.keys()):
        if key not in keep_set and key != "_order":
            history.pop(key)

    return history


def create_branch(
    github_repository: str,
    from_branch: str,
    to_branch: str, 
    restart_from_subgraph: str, 
    client: GithubClient | None = None,
) -> bool:
    client = client or GithubClient()

    if "/" in github_repository:
        github_owner, repository_name = github_repository.split("/", 1)
    else:
        raise ValueError("Invalid repository name format.")

    base_info = client.get_branch(
        github_owner, repository_name, from_branch
    )
    if base_info is None:
        raise RuntimeError(
            f"Branch '{from_branch}' not found in {github_owner}/{repository_name}"
        )

    sha = base_info["commit"]["sha"]
    ok = client.create_branch(
        github_owner, repository_name, to_branch, from_sha=sha
    )

    if not ok:
        logger.error(f"Failed to create branch {to_branch}")
        return False
    
    research_history = github_download(
        github_owner=github_owner,
        repository_name=repository_name,
        branch_name=from_branch,
    )

    pruned_history = _prune_history(research_history, restart_from_subgraph)

    success = github_upload(
        github_owner=github_owner,
        repository_name=repository_name,
        branch_name=to_branch,
        research_history=pruned_history,
        commit_message=f"[branch:{to_branch}] truncate at {restart_from_subgraph}",
    )
    if success:
        print(
            f"Created new branch '{to_branch}' from '{from_branch}' "
            f"and pruned history up to {restart_from_subgraph}"
        )
    return ok


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="CreateBranch")
    parser.add_argument("github_repository", help="Your GitHub repository")
    parser.add_argument("from_branch", help="Branch to create from")
    parser.add_argument("to_branch", help="Name of new branch to create")
    parser.add_argument("restart_from_subgraph", help="Subgraph name to keep up to")

    args = parser.parse_args()

    result = create_branch(
        github_repository=args.github_repository,
        from_branch=args.from_branch,
        to_branch=args.to_branch,
        restart_from_subgraph=args.restart_from_subgraph,
    )
    print(f"result: {result}")
