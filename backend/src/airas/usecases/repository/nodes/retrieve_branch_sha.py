from airas.core.types.github import GitHubConfig
from airas.infra.github_client import GithubClient


def retrieve_branch_sha(
    github_config: GitHubConfig,
    github_client: GithubClient,
    branch_name: str,
) -> str | None:
    response = github_client.get_branch(
        github_owner=github_config.github_owner,
        repository_name=github_config.repository_name,
        branch_name=branch_name,
    )

    if not isinstance(response, dict):
        return None

    return response.get("commit", {}).get("sha") or None
