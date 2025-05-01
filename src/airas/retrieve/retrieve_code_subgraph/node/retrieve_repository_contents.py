import re
import logging

from tenacity import retry, stop_after_attempt, wait_fixed, retry_if_exception_type
import requests

from airas.utils.api_client.github_client import GithubClient
from airas.utils.logging_utils import setup_logging

setup_logging()
logger = logging.getLogger(__name__)

github_client = GithubClient()


@retry(
    retry=retry_if_exception_type(requests.exceptions.ConnectionError),
    stop=stop_after_attempt(3),
    wait=wait_fixed(1),
)
def _retrieve_file_contents(
    repository_owner: str, repository_name: str, file_path: str
):
    content = github_client.get_repository_content(
        repository_owner=repository_owner,
        repository_name=repository_name,
        file_path=file_path,
    )
    return content


@retry(
    retry=retry_if_exception_type(requests.exceptions.ConnectionError),
    stop=stop_after_attempt(3),
    wait=wait_fixed(1),
)
def _retrieve_repository_tree(
    repository_owner: str, repository_name: str, tree_sha: str
):
    tree = github_client.get_a_tree(
        repository_owner=repository_owner,
        repository_name=repository_name,
        tree_sha=tree_sha,
    )
    return tree


def retrieve_repository_contents(github_url: str) -> str:
    match = re.match(r"https://github\.com/([^/]+)/([^/]+)", github_url)
    if match:
        repository_owner = match.group(1)
        repository_name = match.group(2)
    else:
        raise ValueError(f"Invalid GitHub URL: {github_url}")

    repository_tree_info = _retrieve_repository_tree(
        repository_owner=repository_owner,
        repository_name=repository_name,
        tree_sha="main",
    )
    if repository_tree_info is None:
        raise RuntimeError(
            f"Failed to retrieve the tree for {repository_owner}/{repository_name}"
        )
    file_path_list = [i.get("path", "") for i in repository_tree_info["tree"]]
    filtered_file_path_list = [
        f for f in file_path_list if f.endswith((".py", ".ipynb"))
    ]
    content_str = ""
    for file_path in filtered_file_path_list:
        content = _retrieve_file_contents(
            repository_owner=repository_owner,
            repository_name=repository_name,
            file_path=file_path,
        )
        if content is None:
            logger.warning(f"Failed to retrieve file data: {file_path}")
        else:
            content_str += f"""\
File Path: {file_path}
content: {content}"""
    return content_str


if __name__ == "__main__":
    repository_owner = "auto-res"
    repository_name = "airas"
    content = retrieve_repository_contents(repository_owner, repository_name)
    print(content)
