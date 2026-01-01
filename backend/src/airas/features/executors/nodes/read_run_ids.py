from logging import getLogger

from airas.services.api_client.github_client import GithubClient
from airas.types.github import GitHubConfig

logger = getLogger(__name__)


async def read_run_ids_from_repository(
    github_client: GithubClient,
    github_config: GitHubConfig,
    config_dir: str = "config/runs",
) -> list[str]:
    try:
        contents = await github_client.aget_repository_content(
            github_config.github_owner,
            github_config.repository_name,
            config_dir,
            branch_name=github_config.branch_name,
        )

        if not contents:
            logger.warning(f"No contents found in {config_dir}")
            return []

        run_ids = []
        for item in contents:
            name = item.get("name", "")
            if item.get("type") == "file" and name.endswith(".yaml"):
                # Remove .yaml extension to get run_id
                run_id = name[:-5]  # Remove ".yaml"
                run_ids.append(run_id)
                logger.debug(f"Found run_id: {run_id}")

        if not run_ids:
            logger.warning(f"No YAML files found in {config_dir}")
            return []

        logger.info(f"Successfully read {len(run_ids)} run_ids from {config_dir}")
        logger.info(f"Run IDs: {', '.join(run_ids)}")
        return run_ids

    except Exception as e:
        logger.error(f"Failed to read run_ids from repository: {e}")
        return []
