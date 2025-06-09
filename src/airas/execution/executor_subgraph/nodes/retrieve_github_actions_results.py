import base64
import logging
import sys

from airas.utils.api_client.github_client import GithubClient

logger = logging.getLogger(__name__)


def _decode_base64_content(content: str) -> str:
    """Decode base64 encoded file content from GitHub API."""
    try:
        decoded_bytes = base64.b64decode(content)
        return decoded_bytes.decode('utf-8')
    except Exception as e:
        logger.error(f"Failed to decode base64 content: {e}")
        raise


def _get_single_file_content(
    client: GithubClient,
    github_owner: str,
    repository_name: str,
    file_path: str,
    branch_name: str
) -> str:
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
            as_="json"
        )
        
        if not response or "content" not in response:
            raise RuntimeError(f"Failed to retrieve {file_path} from repository")
        
        content = _decode_base64_content(response["content"])
        logger.info(f"Retrieved {file_path} from repository")
        return content
        
    except Exception as e:
        logger.error(f"Error retrieving {file_path} from repository: {e}")
        raise


def retrieve_github_actions_results(
    github_owner: str,
    repository_name: str,
    branch_name: str,
    experiment_iteration: int,
) -> tuple[str, str]:
    """
    Retrieve output.txt and error.txt files from .research/iteration1/ directory in the repository.
    
    Args:
        github_owner: GitHub repository owner
        repository_name: Repository name
        branch_name: Branch name to retrieve files from
        client: GitHub client instance (optional)
        
    Returns:
        Tuple of (output_text_data, error_text_data)
    """
    client = GithubClient()

    output_file_path = f".research/iteration{experiment_iteration}/output.txt"
    error_file_path = f".research/iteration{experiment_iteration}/error.txt"

    # Get both files using the helper function
    output_text_data = _get_single_file_content(
        client, github_owner, repository_name, output_file_path, branch_name
    )
    
    error_text_data = _get_single_file_content(
        client, github_owner, repository_name, error_file_path, branch_name
    )

    return output_text_data, error_text_data


def main():
    """Main function to demonstrate the usage of retrieve_repository_files."""
    # Setup logging for demonstration
    logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
    
    # Example usage - replace with actual values
    github_owner = "fuyu-quant"
    repository_name = "airas-temp"
    branch_name = "main"
    
    print("Retrieving repository files...")
    print(f"Owner: {github_owner}")
    print(f"Repository: {repository_name}")
    print(f"Branch: {branch_name}")
    print("-" * 50)
    
    try:
        output_data, error_data = retrieve_github_actions_results(
            github_owner=github_owner,
            repository_name=repository_name,
            branch_name=branch_name
        )
        
        print("Successfully retrieved files!")
        print(f"Output data length: {len(output_data)} characters")
        print(f"Error data length: {len(error_data)} characters")
        
        # Display first 200 characters of each file
        print("\nOutput file preview:")
        print(output_data[:200] + "..." if len(output_data) > 200 else output_data)
        
        print("\nError file preview:")
        print(error_data[:200] + "..." if len(error_data) > 200 else error_data)
        
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
