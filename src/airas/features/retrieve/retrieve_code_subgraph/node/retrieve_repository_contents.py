import base64
import logging
import re

from airas.services.api_client.github_client import GithubClient, GithubClientFatalError
from airas.types.research_study import ResearchStudy
from airas.utils.logging_utils import setup_logging

setup_logging()
logger = logging.getLogger(__name__)


def _parse_github_url(github_url: str) -> tuple[str, str] | None:
    match = re.match(r"https://github\.com/([^/]+)/([^/]+)", github_url)
    if not match:
        return None
    return match.group(1), match.group(2)


def _get_python_files(
    client: GithubClient, github_owner: str, repository_name: str, default_branch: str
) -> list[str]:
    try:
        repository_tree_info = client.get_a_tree(
            github_owner=github_owner,
            repository_name=repository_name,
            tree_sha=default_branch,
        )

        if repository_tree_info is None:
            return []

        return [
            entry.get("path", "")
            for entry in repository_tree_info["tree"]
            if entry.get("path", "").endswith((".py"))
        ]
    except Exception as e:
        logger.warning(f"Failed to retrieve repository tree: {e}")
        return []


def _get_file_content(
    client: GithubClient, github_owner: str, repository_name: str, file_path: str
) -> str:
    try:
        file_bytes = client.get_repository_content(
            github_owner=github_owner,
            repository_name=repository_name,
            file_path=file_path,
        )
    except GithubClientFatalError:
        # Re-raise fatal errors so they can be caught at repository level
        raise
    except Exception as e:
        logger.warning(f"Error retrieving file {file_path}: {e}")
        return ""

    if file_bytes is None:
        logger.warning(f"Failed to retrieve file data: {file_path}")
        return ""

    content_b64 = file_bytes.get("content", "")
    content_b64 = content_b64.replace("\\n", "\n")
    decoded_bytes = base64.b64decode(content_b64)

    try:
        content_str = decoded_bytes.decode("utf-8")
    except Exception as e:
        logger.warning(f"Failed to decode file content: {e}")
        return ""

    return f"File Path: {file_path}\nContent:\n{content_str}"


def _retrieve_single_repository_contents(
    client: GithubClient, github_url: str, title: str
) -> str:
    if not (url_parts := _parse_github_url(github_url)):
        logger.warning(f"Invalid GitHub URL format for '{title}': {github_url}")
        return ""

    github_owner, repository_name = url_parts

    try:
        response = client.get_repository(github_owner, repository_name)
    except Exception as e:
        logger.error(f"Error retrieving repository contents for '{title}': {e}")
        return ""

    if not response:
        logger.warning(f"Failed to get repository info for '{title}': {github_url}")
        return ""

    default_branch = response.get("default_branch", "master")
    file_paths = _get_python_files(
        client, github_owner, repository_name, default_branch
    )
    if not file_paths:
        logger.info(f"No Python files found for '{title}': {github_url}")
        return ""

    contents = []
    for file_path in file_paths:
        try:
            content = _get_file_content(
                client, github_owner, repository_name, file_path
            )
            if content:
                contents.append(content)
        except GithubClientFatalError:
            logger.warning(
                f"Fatal error for repository '{title}': {github_url}. Skipping remaining files in repository."
            )
            return ""  # NOTE: Skip this repository on FatalError, as subsequent file contents cannot be retrieved.
        except Exception as e:
            logger.warning(f"Error retrieving file {file_path}: {e}")

    logger.info(
        f"Successfully retrieved repository contents for '{title}': {len(file_paths)} files"
    )
    return "\n".join(contents)


def retrieve_repository_contents(research_study_list: list[ResearchStudy]) -> list[str]:
    code_str_list = []
    client = GithubClient()

    for research_study in research_study_list:
        title = research_study.title or "N/A"

        if not research_study.meta_data or not research_study.meta_data.github_url:
            logger.info(
                f"No GitHub URL for '{title}', skipping repository content retrieval."
            )
            code_str_list.append("")
            continue

        github_url = research_study.meta_data.github_url
        content = _retrieve_single_repository_contents(client, github_url, title)
        code_str_list.append(content)

    return code_str_list
