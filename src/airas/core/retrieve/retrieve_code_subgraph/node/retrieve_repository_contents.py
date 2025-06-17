import logging
import re

from airas.services.api_client.github_client import GithubClient
from airas.utils.logging_utils import setup_logging

setup_logging()
logger = logging.getLogger(__name__)


def retrieve_repository_contents(github_url: str) -> str:
    match = re.match(r"https://github\.com/([^/]+)/([^/]+)", github_url)
    if not match:
        raise ValueError(f"Invalid GitHub URL: {github_url}")
    github_owner, repository_name = match.group(1), match.group(2)

    client = GithubClient()
    response = client.get_repository(github_owner, repository_name)
    if not response:
        return ""
    
    default_branch = response.get("default_branch", "master") # or `main``
    try:
        repository_tree_info = client.get_a_tree(
            github_owner=github_owner,
            repository_name=repository_name,
            tree_sha=default_branch,
        )
    except Exception as e:
        logger.warning(f"Failed to retrieve repository tree: {e}")
        return ""

    if repository_tree_info is None:
        return ""
    

    file_paths = [
        entry.get("path", "")
        for entry in repository_tree_info["tree"]
        if entry.get("path", "").endswith((".py", ".ipynb"))
    ]

    contents = []
    for file_path in file_paths:
        file_bytes = client.get_repository_content(
            github_owner=github_owner,
            repository_name=repository_name,
            file_path=file_path,
        )
        if file_bytes is None:
            logger.warning(f"Failed to retrieve file data: {file_path}")
            continue
        try:
            content_str = file_bytes.decode("utf-8")
        except AttributeError:
            content_str = str(file_bytes)
        contents.append(
            f"File Path: {file_path}\nContent:\n{content_str}"
        )
    return "\n".join(contents)
