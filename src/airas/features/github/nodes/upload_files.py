import logging
import os

from dependency_injector.wiring import Provide, inject

from airas.services.api_client.api_clients_container import APIClientsContainer
from airas.services.api_client.github_client import GithubClient

logger = logging.getLogger(__name__)


def _upload_single_file(
    github_owner: str,
    repository_name: str,
    branch_name: str,
    upload_dir: str,
    local_path: str,
    commit_message: str,
    client: GithubClient,
) -> bool:
    try:
        with open(local_path, "rb") as f:
            content = f.read()

        target_path = os.path.join(upload_dir, os.path.basename(local_path)).replace(
            "\\", "/"
        )

        ok = client.commit_file_bytes(
            github_owner=github_owner,
            repository_name=repository_name,
            branch_name=branch_name,
            file_path=target_path,
            file_content=content,
            commit_message=commit_message,
        )
        return ok
    except Exception as e:
        logger.warning(f"Asset upload failed: {local_path} ({e})")
        return False


@inject
def upload_files(
    github_owner: str,
    repository_name: str,
    branch_name: str,
    upload_dir: str,
    local_file_paths: list[str],
    commit_message: str = "Upload files",
    client: GithubClient = Provide[APIClientsContainer.github_client],
) -> bool:
    if not isinstance(local_file_paths, list):
        raise TypeError("local_file_paths must be a list of file paths")
    upload_dir = upload_dir.replace("\\", "/")

    results = [
        _upload_single_file(
            github_owner=github_owner,
            repository_name=repository_name,
            branch_name=branch_name,
            upload_dir=upload_dir,
            local_path=path,
            commit_message=commit_message,
            client=client,
        )
        for path in local_file_paths
    ]

    return all(results)
