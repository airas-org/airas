from logging import getLogger
from typing import Any, Iterator

from airas.services.api_client.github_client import GithubClient

logger = getLogger(__name__)


def _iter_commits(
    github_owner: str, 
    repository_name: str, 
    branch_name: str, 
    per_page: int = 100, 
    max_pages: int = 10, 
    *, 
    client: GithubClient, 
) -> Iterator[dict[str, Any]]:
    page = 1
    while max_pages is None or page <= max_pages:
        commits = client.list_commits(
            github_owner,
            repository_name,
            sha=branch_name,
            per_page=per_page,
            page=page,
        )

        if not commits:
            break

        yield from commits
        page += 1
    

def find_commit_sha(
    github_owner: str, 
    repository_name: str, 
    branch_name: str, 
    subgraph_name: str, 
    max_pages: int = 10, 
    client: GithubClient | None = None, 
) -> str:
    client = client or GithubClient()
    marker = f"[subgraph: {subgraph_name}]"
    try:
        target_sha = next(
            commit["sha"]
            for commit in _iter_commits(
                github_owner,
                repository_name,
                branch_name,
                max_pages, 
                client=client,
            )
            if marker in commit["commit"]["message"]
        )
        logger.info(
            f"Found commit {target_sha} for subgraph {subgraph_name} on branch {branch_name}."
        )
        return target_sha
    except StopIteration:
        raise RuntimeError(
            f"Commit containing marker '{marker}' not found in branch '{branch_name}'."
        ) from None