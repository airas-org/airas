import logging
import os

from dependency_injector.wiring import Provide, inject

from airas.services.api_client.api_clients_container import SyncContainer
from airas.services.api_client.github_client import GithubClient, GithubClientError
from airas.types.github import GitHubRepositoryInfo

logger = logging.getLogger(__name__)


@inject
def set_github_actions_secrets(
    github_repository_info: GitHubRepositoryInfo,
    secret_names: list[str],
    github_client: GithubClient = Provide[SyncContainer.github_client],
) -> bool:
    try:
        # Get repository public key once for all secrets
        public_key_info = github_client.get_repository_public_key(
            github_owner=github_repository_info.github_owner,
            repository_name=github_repository_info.repository_name,
        )
        if not public_key_info:
            logger.error(
                f"Failed to get public key for repository {github_repository_info.github_owner}/{github_repository_info.repository_name}"
            )
            return False

        success_count = 0
        for secret_name in secret_names:
            token_value = os.getenv(secret_name)
            if not token_value:
                logger.warning(
                    f"Token '{secret_name}' not found in environment variables, skipping"
                )
                continue

            logger.info(f"Token '{secret_name}' retrieved from environment variables")

            success = github_client.create_or_update_repository_secret(
                github_owner=github_repository_info.github_owner,
                repository_name=github_repository_info.repository_name,
                secret_name=secret_name,
                secret_value=token_value,
                public_key_info=public_key_info,
            )

            if success:
                logger.info(
                    f"Successfully set GitHub Actions secret '{secret_name}' for {github_repository_info.github_owner}/{github_repository_info.repository_name}"
                )
                success_count += 1
            else:
                logger.error(
                    f"Failed to set GitHub Actions secret '{secret_name}' for {github_repository_info.github_owner}/{github_repository_info.repository_name}"
                )

        logger.info(f"Successfully set {success_count}/{len(secret_names)} secrets")
        return success_count > 0

    except GithubClientError as e:
        logger.error(f"GitHub API error while setting secrets: {e}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error while setting GitHub Actions secrets: {e}")
        return False
