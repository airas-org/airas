from logging import getLogger
from typing import Any, Iterator

from dependency_injector.wiring import Provide, inject

from airas.services.api_client.api_clients_container import SyncContainer
from airas.services.api_client.github_client import GithubClient
from airas.types.github import GitHubRepositoryInfo

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


@inject
def find_commit_sha(
    github_repository_info: GitHubRepositoryInfo,
    subgraph_name: str,
    max_pages: int = 10,
    client: GithubClient = Provide[SyncContainer.github_client],
) -> str:
    marker = f"[subgraph: {subgraph_name}]"

    commits_iter = _iter_commits(
        github_repository_info.github_owner,
        github_repository_info.repository_name,
        github_repository_info.branch_name,
        max_pages,
        client=client,
    )

    try:
        # Find the commit with the marker
        for commit in commits_iter:
            if marker in commit["commit"]["message"]:
                # Get the next commit (parent commit)
                parent_commit = next(commits_iter)
                logger.info(
                    f"Found parent commit {parent_commit['sha']} before subgraph {subgraph_name} on branch {github_repository_info.branch_name}."
                )
                return parent_commit["sha"]

        raise RuntimeError(
            f"Commit containing marker '{marker}' not found in branch '{github_repository_info.branch_name}'."
        )
    except StopIteration:
        raise RuntimeError(
            f"No parent commit found before subgraph '{subgraph_name}' on branch '{github_repository_info.branch_name}'."
        ) from None
