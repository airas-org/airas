import asyncio
from logging import getLogger

from airas.services.api_client.github_client import GithubClient
from airas.types.github import GitHubConfig

logger = getLogger(__name__)


async def create_branch(
    github_client: GithubClient,
    github_owner: str,
    repository_name: str,
    new_branch_name: str,
    from_sha: str,
) -> bool:
    existing_branch = await github_client.aget_branch(
        github_owner=github_owner,
        repository_name=repository_name,
        branch_name=new_branch_name,
    )

    if existing_branch:
        logger.info(
            f"Branch '{new_branch_name}' already exists in repository "
            f"'{github_owner}/{repository_name}'. Skipping creation."
        )
        return True

    try:
        response = await github_client.acreate_branch(
            github_owner=github_owner,
            repository_name=repository_name,
            branch_name=new_branch_name,
            from_sha=from_sha,
        )

        if response:
            logger.info(
                f"Branch '{new_branch_name}' successfully created in "
                f"'{github_owner}/{repository_name}' from '{from_sha}'"
            )
            return True
        else:
            logger.error(
                f"Failed to create branch '{new_branch_name}'. API returned empty response."
            )
            return False

    except Exception as e:
        logger.error(
            f"Error creating branch '{new_branch_name}' in "
            f"'{github_owner}/{repository_name}': {e}"
        )
        return False


async def create_branches_for_run_ids(
    github_client: GithubClient,
    github_config: GitHubConfig,
    run_ids: list[str],
) -> list[tuple[str, str, bool]]:
    if not run_ids:
        logger.warning("No run_ids provided.")
        return []

    base_branch_info = await github_client.aget_branch(
        github_config.github_owner,
        github_config.repository_name,
        github_config.branch_name,
    )
    if not base_branch_info:
        raise ValueError(f"Base branch '{github_config.branch_name}' not found.")

    base_commit_sha = base_branch_info["commit"]["sha"]

    tasks = []
    results_map = []

    for run_id in run_ids:
        child_branch = f"{github_config.branch_name}-{run_id}"
        results_map.append((run_id, child_branch))

        task = create_branch(
            github_client=github_client,
            github_owner=github_config.github_owner,
            repository_name=github_config.repository_name,
            new_branch_name=child_branch,
            from_sha=base_commit_sha,
        )
        tasks.append(task)

    success_results = await asyncio.gather(*tasks)

    return [
        (run_id, branch_name, is_success)
        for (run_id, branch_name), is_success in zip(
            results_map, success_results, strict=True
        )
    ]
