import base64
import logging
import sys
from typing import cast

from airas.services.api_client.github_client import GithubClient
from airas.types.github import GitHubRepositoryInfo

logger = logging.getLogger(__name__)


def _decode_base64_content(content: str) -> str:
    """Decode base64 encoded file content from GitHub API."""
    try:
        decoded_bytes = base64.b64decode(content)
        return decoded_bytes.decode("utf-8")
    except Exception as e:
        logger.error(f"Failed to decode base64 content: {e}")
        raise


def _get_single_file_content(
    client: GithubClient,
    github_owner: str,
    repository_name: str,
    file_path: str,
    branch_name: str,
) -> dict | bytes:
    """
    Retrieve a single file content from the repository.

    Args:
        client: GitHub client instance
        github_owner: GitHub repository owner
        repository_name: Repository name
        file_path: Path to the file in the repository
        branch_name: Branch name to retrieve file from

    Returns:
        Decoded file content as string

    Raises:
        RuntimeError: If file retrieval fails
    """
    try:
        response = client.get_repository_content(
            github_owner=github_owner,
            repository_name=repository_name,
            file_path=file_path,
            branch_name=branch_name,
            as_="json",
        )
        return response

    except Exception as e:
        logger.error(f"Error retrieving {file_path} from repository: {e}")
        raise


def retrieve_github_actions_results(
    github_repository: GitHubRepositoryInfo,
    experiment_iteration: int,
    github_client: GithubClient | None = None,
) -> tuple[str, str, list[str]]:
    """
    Retrieve output.txt and error.txt files from .research/iteration1/ directory in the repository.

    Args:
        github_repository: Full GitHub repository name in the format "owner/repository"
        branch_name: Branch name to retrieve files from
        client: GitHub client instance (optional)

    Returns:
        Tuple of (output_text_data, error_text_data)
    """
    client = github_client or GithubClient()

    github_owner = github_repository.github_owner
    repository_name = github_repository.repository_name
    branch_name = github_repository.branch_name

    output_file_path = f".research/iteration{experiment_iteration}/output.txt"
    error_file_path = f".research/iteration{experiment_iteration}/error.txt"
    image_directory_path = f".research/iteration{experiment_iteration}/images"

    # Get both files using the helper function
    output_text_response = _get_single_file_content(
        client, github_owner, repository_name, output_file_path, branch_name
    )
    if not output_text_response or "content" not in output_text_response:
        raise RuntimeError(f"Failed to retrieve {output_file_path} from repository")
    output_text_data = _decode_base64_content(output_text_response["content"])

    error_text_data = _get_single_file_content(
        client, github_owner, repository_name, error_file_path, branch_name
    )
    if not error_text_data or "content" not in error_text_data:
        raise RuntimeError(f"Failed to retrieve {error_file_path} from repository")
    error_text_data = _decode_base64_content(error_text_data["content"])

    try:
        image_data_list = _get_single_file_content(
            client, github_owner, repository_name, image_directory_path, branch_name
        )
        image_file_name_list = [
            image_data["name"] for image_data in cast(list[dict], image_data_list)
        ]
    except Exception as e:
        logger.warning(f"Images directory not found at {image_directory_path}: {e}")
        image_file_name_list = []

    return output_text_data, error_text_data, image_file_name_list


def main():
    """Main function to demonstrate the usage of retrieve_repository_files."""
    # Setup logging for demonstration
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

    # Example usage - replace with actual values
    github_repository = {
        "github_owner": "auto-res2",
        "repository_name": "test-tanaka-v6",
        "branch_name": "develop-1",
    }

    try:
        output_data, error_data, image_data = retrieve_github_actions_results(
            github_repository=github_repository,
            experiment_iteration=1,  # Example iteration
        )

        print("Successfully retrieved files!")
        print(f"Output data length: {len(output_data)} characters")
        print(f"Error data length: {len(error_data)} characters")

        # Display first 200 characters of each file
        print("\nOutput file preview:")
        print(output_data[:200] + "..." if len(output_data) > 200 else output_data)

        print("\nError file preview:")
        print(error_data[:200] + "..." if len(error_data) > 200 else error_data)

        print("\nImage files list:")
        for image_file in image_data:
            print(f"- {image_file}")

    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
