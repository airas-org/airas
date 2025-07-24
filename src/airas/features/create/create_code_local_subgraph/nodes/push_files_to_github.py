import logging
from typing import Dict

from airas.services.api_client.github_client import GithubClient

logger = logging.getLogger(__name__)


def push_files_to_github(
    github_repository: str,
    branch_name: str,
    files: Dict[str, str],
    commit_message: str,
    github_client: GithubClient | None = None,
) -> bool:
    """Push multiple files to GitHub repository using Git Data API"""

    if github_client is None:
        github_client = GithubClient()

    try:
        # Parse repository owner and name
        if "/" not in github_repository:
            raise ValueError(
                f"Invalid repository format: {github_repository}. Expected 'owner/repo'"
            )

        github_owner, repository_name = github_repository.split("/", 1)

        logger.info(f"Pushing {len(files)} files to {github_repository}:{branch_name}")

        # Use the new commit_multiple_files method
        success = github_client.commit_multiple_files(
            github_owner=github_owner,
            repository_name=repository_name,
            branch_name=branch_name,
            files=files,
            commit_message=commit_message,
        )

        if success:
            logger.info(
                f"Successfully pushed files to {github_repository}:{branch_name}"
            )
            return True
        else:
            logger.error(f"Failed to push files to {github_repository}:{branch_name}")
            return False

    except Exception as e:
        logger.error(f"Error pushing files to GitHub: {e}")
        return False


if __name__ == "__main__":
    # Test the function
    test_files = {
        "src/test.py": "print('Hello, world!')",
        "requirements.txt": "numpy==1.21.0\npandas==1.3.0",
    }

    result = push_files_to_github(
        github_repository="test-owner/test-repo",
        branch_name="develop",
        files=test_files,
        commit_message="Add generated experiment files",
    )
    print(f"Push result: {result}")
