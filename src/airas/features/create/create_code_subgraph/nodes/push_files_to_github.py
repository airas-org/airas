import logging

from airas.services.api_client.github_client import GithubClient

logger = logging.getLogger(__name__)


def push_files_to_github(
    github_repository: dict[str, str],
    files: dict[str, str],
    commit_message: str,
    github_client: GithubClient | None = None,
) -> bool:
    """Push multiple files to GitHub repository using Git Data API"""
    github_client = github_client or GithubClient()

    # Use the new commit_multiple_files method
    success = github_client.commit_multiple_files(
        github_owner=github_repository["github_owner"],
        repository_name=github_repository["repository_name"],
        branch_name=github_repository["branch_name"],
        files=files,
        commit_message=commit_message,
    )

    if success:
        logger.info(
            f"Successfully pushed files to {github_repository['github_owner']}/{github_repository['repository_name']} on branch {github_repository['branch_name']}"
        )
        # created_files = list(state["generated_files"].keys()) if success else []
        return True
    else:
        logger.error(
            f"Failed to push files to {github_repository['github_owner']}/{github_repository['repository_name']} on branch {github_repository['branch_name']}"
        )
        return False


if __name__ == "__main__":
    # Test the function
    test_files = {
        "src/test.py": "print('Hello, world!')",
        "requirements.txt": "numpy==1.21.0\npandas==1.3.0",
    }

    github_repository = {
        "github_owner": "test-owner",
        "repository_name": "test-repo",
        "branch_name": "develop",
    }
    result = push_files_to_github(
        github_repository=github_repository,
        files=test_files,
        commit_message="Add generated experiment files",
    )
    print(f"Push result: {result}")
