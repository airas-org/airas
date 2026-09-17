import asyncio

from airas.core.types.github import GitHubConfig
from airas.infra.github.nodes.set_github_actions_secrets import (
    set_github_actions_secrets as set_secrets_on_github,
)
from airas.infra.github_client import GithubClient


async def set_github_actions_secrets(
    github_config: GitHubConfig,
    *,
    github_client: GithubClient,
    secret_names: list[str] | None = None,
) -> bool:
    return await asyncio.to_thread(
        set_secrets_on_github,
        github_config=github_config,
        github_client=github_client,
        secret_names=secret_names,
    )
