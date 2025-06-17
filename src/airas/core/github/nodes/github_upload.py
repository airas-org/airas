import json
import logging
import time
from typing import Any

from airas.services.api_client.github_client import GithubClient

logger = logging.getLogger(__name__)


def github_upload(
    github_owner: str,
    repository_name: str,
    branch_name: str,
    research_history: dict[str, Any],
    file_path: str = ".research/research_history.json",
    commit_message: str = "Update history via github_upload",
    wait_seconds: float = 3.0, 
    client: GithubClient | None = None,
) -> bool:
    if client is None:
        client = GithubClient()

    logger.info(f"[GitHub I/O] Upload: {github_owner}/{repository_name}@{branch_name}:{file_path}")
    ok_json = client.commit_file_bytes(
        github_owner=github_owner,
        repository_name=repository_name,
        branch_name=branch_name,
        file_path=file_path,
        file_content=json.dumps(research_history, ensure_ascii=False, indent=2).encode(),
        commit_message=commit_message,
    )
    if ok_json:
        print(f"Check here：https://github.com/{github_owner}/{repository_name}/blob/{branch_name}/{file_path}")

    if wait_seconds > 0:
        time.sleep(wait_seconds)
    return ok_json
