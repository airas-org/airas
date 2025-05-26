import logging
from datetime import datetime, timezone

from airas.utils.api_client.github_client import GithubClient

logger = logging.getLogger(__name__)


def prepare_branch(
    github_owner: str,
    repository_name: str,
    branch_name: str,
    subgraph_name: str | None, 
    client: GithubClient | None = None,
) -> str:
    if client is None:
        client = GithubClient()

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
    print(f"Created new branch '{new_branch}' from '{branch_name}'")
    return new_branch