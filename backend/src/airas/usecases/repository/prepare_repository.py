import asyncio
from typing import Any

from airas.core.types.github import GitHubConfig
from airas.infra.github.nodes.create_branch import create_branch
from airas.infra.github_client import GithubClient
from airas.usecases.repository.nodes.check_repository_from_template import (
    check_repository_from_template,
)
from airas.usecases.repository.nodes.create_repository_from_template import (
    create_repository_from_template,
)
from airas.usecases.repository.nodes.protect_branch import protect_branch
from airas.usecases.repository.nodes.retrieve_branch_sha import (
    retrieve_branch_sha,
)

TEMPLATE_OWNER = "airas-org"
TEMPLATE_REPO = "airas-template"
TEMPLATE_DEFAULT_BRANCH = "main"

# GitHub fills a template repository's contents asynchronously.
_TEMPLATE_SETTLE_SECONDS = 5


async def prepare_repository(
    github_config: GitHubConfig,
    *,
    github_client: GithubClient,
    is_private: bool = False,
    protected_branch: str | None = None,
) -> dict[str, Any]:
    protected_branch = protected_branch or github_config.branch_name

    exists = await asyncio.to_thread(
        check_repository_from_template,
        github_config=github_config,
        github_client=github_client,
        template_owner=TEMPLATE_OWNER,
        template_repo=TEMPLATE_REPO,
    )
    if not exists:
        await asyncio.to_thread(
            create_repository_from_template,
            github_config=github_config,
            github_client=github_client,
            template_owner=TEMPLATE_OWNER,
            template_repo=TEMPLATE_REPO,
            is_github_repo_private=is_private,
        )
        await asyncio.sleep(_TEMPLATE_SETTLE_SECONDS)

    branch_ready = (
        await asyncio.to_thread(
            retrieve_branch_sha,
            github_config=github_config,
            github_client=github_client,
            branch_name=github_config.branch_name,
        )
        is not None
    )
    if not branch_ready:
        base_sha = await asyncio.to_thread(
            retrieve_branch_sha,
            github_config=github_config,
            github_client=github_client,
            branch_name=TEMPLATE_DEFAULT_BRANCH,
        )
        if base_sha is None:
            raise RuntimeError(
                f"Branch '{TEMPLATE_DEFAULT_BRANCH}' not found in "
                f"{github_config.github_owner}/{github_config.repository_name}"
            )
        branch_ready = await create_branch(
            github_client=github_client,
            github_owner=github_config.github_owner,
            repository_name=github_config.repository_name,
            new_branch_name=github_config.branch_name,
            from_sha=base_sha,
        )

    # A CI step that fails is reported, never fatal: the repository exists.
    warnings: list[str] = []
    branch_protected = False
    merge_settings_updated = False
    pages_enabled = False
    try:
        branch_protected, merge_settings_updated = await protect_branch(
            github_config, protected_branch, github_client=github_client
        )
    except Exception as e:
        warnings.append(
            f"'{protected_branch}' was not protected ({e}). Nothing "
            "prevents a red or unchecked commit from landing on it, so "
            "the record's guarantees are advisory in this repository "
            "until it is fixed: re-run prepare_repository once the token "
            "has admin rights."
        )
    try:
        pages_enabled = await github_client.aenable_pages_from_actions(
            github_config.github_owner, github_config.repository_name
        )
    except Exception as e:
        warnings.append(
            f"GitHub Pages was not pointed at Actions ({e}); the Publish "
            "HTML workflow will have nowhere to deploy until the "
            "repository's Pages source is set to GitHub Actions."
        )

    repository = f"{github_config.github_owner}/{github_config.repository_name}"
    return {
        "is_repository_ready": True,
        "is_branch_ready": branch_ready,
        "html_url": f"https://github.com/{repository}",
        "clone_url": f"https://github.com/{repository}.git",
        "branch_protected": branch_protected,
        "merge_settings_updated": merge_settings_updated,
        "pages_enabled": pages_enabled,
        "protected_branch": protected_branch if branch_protected else None,
        "warnings": warnings,
    }
