import base64
import logging
from typing import Dict, List

from airas.services.api_client.github_client import GithubClient

logger = logging.getLogger(__name__)


def get_current_files(
    github_repository: str,
    branch_name: str,
    file_paths: List[str],
    github_client: GithubClient | None = None,
) -> Dict[str, str]:
    """Get current content of specified files from GitHub repository"""

    if github_client is None:
        github_client = GithubClient()

    files_content = {}

    try:
        # Parse repository owner and name
        if "/" not in github_repository:
            raise ValueError(
                f"Invalid repository format: {github_repository}. Expected 'owner/repo'"
            )

        github_owner, repository_name = github_repository.split("/", 1)

        logger.info(
            f"Getting {len(file_paths)} files from {github_repository}:{branch_name}"
        )

        for file_path in file_paths:
            try:
                # Get file content
                content = github_client.get_repository_content(
                    github_owner=github_owner,
                    repository_name=repository_name,
                    file_path=file_path,
                    branch_name=branch_name,
                    as_="json",
                )

                if isinstance(content, dict) and "content" in content:
                    # Decode base64 content
                    decoded_content = base64.b64decode(content["content"]).decode(
                        "utf-8"
                    )
                    files_content[file_path] = decoded_content
                    logger.info(f"Successfully retrieved {file_path}")
                else:
                    logger.warning(f"Unexpected content format for {file_path}")

            except Exception as e:
                logger.warning(f"Failed to get {file_path}: {e}")
                # Continue with other files even if one fails
                continue

        logger.info(
            f"Successfully retrieved {len(files_content)} out of {len(file_paths)} files"
        )
        return files_content

    except Exception as e:
        logger.error(f"Error getting current files: {e}")
        return {}


def get_python_files_from_error(error_text: str) -> List[str]:
    """Extract Python file paths from error messages"""
    import re

    # Common patterns for Python file paths in error messages
    patterns = [
        r'File "([^"]+\.py)"',  # File "path/to/file.py"
        r"in ([^\s]+\.py)",  # in file.py
        r"([^\s]+\.py):\d+",  # file.py:123
        r"src/([^\s]+\.py)",  # src/file.py
    ]

    file_paths = set()

    for pattern in patterns:
        matches = re.findall(pattern, error_text)
        for match in matches:
            # Clean up the path
            if match.startswith("./"):
                match = match[2:]
            if not match.startswith("src/") and "/" not in match:
                match = f"src/{match}"
            file_paths.add(match)

    # Add common files that might need fixing
    common_files = [
        "src/main.py",
        "src/train.py",
        "src/evaluate.py",
        "src/preprocess.py",
        "requirements.txt",
    ]

    file_paths.update(common_files)

    return list(file_paths)


if __name__ == "__main__":
    # Test the function
    test_files = ["src/main.py", "src/train.py", "requirements.txt"]

    result = get_current_files(
        github_repository="test-owner/test-repo",
        branch_name="develop",
        file_paths=test_files,
    )
    print(f"Retrieved files: {list(result.keys())}")

    # Test error parsing
    error_text = (
        'File "src/train.py", line 10, in <module>\nImportError: No module named numpy'
    )
    files = get_python_files_from_error(error_text)
    print(f"Files from error: {files}")
