import argparse
import json
import logging
import os
import time
from typing import Any

from typing_extensions import TypedDict

from airas.utils.api_client.github_client import GithubClient

logger = logging.getLogger(__name__)


class ExtraFileConfig(TypedDict):
    upload_branch: str
    upload_dir: str
    local_file_paths: list[str]


def _commit_assets(
    extra_files: list[ExtraFileConfig],
    github_owner: str,
    repository_name: str,
    client: GithubClient,
    commit_message: str,
) -> bool:
    success = True
    for cfg in extra_files:
        branch = cfg["upload_branch"]
        directory = cfg["upload_dir"].replace("\\", "/")
        for local_path in cfg["local_file_paths"]:
            try:
                with open(local_path, "rb") as f:
                    content = f.read()
                target_path = os.path.join(directory, os.path.basename(local_path)).replace("\\", "/")
                ok = client.commit_file_bytes(
                    github_owner=github_owner,
                    repository_name=repository_name,
                    branch_name=branch,
                    file_path=target_path,
                    file_content=content,
                    commit_message=commit_message,
                )
                success &= ok
            except Exception as e:
                logger.warning(f"Asset upload failed: {local_path} ({e})")
                success = False
    return success


def github_upload(
    github_owner: str,
    repository_name: str,
    branch_name: str,
    research_history: dict[str, Any],
    file_path: str | None = ".research/research_history.json",
    extra_files: list[ExtraFileConfig] | None = None,
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

    ok_assets = True
    if extra_files:
        ok_assets = _commit_assets(
            extra_files,
            github_owner,
            repository_name,
            client,
            commit_message=commit_message,
        )
    if wait_seconds > 0:
        time.sleep(wait_seconds)
    return ok_json and ok_assets


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="github_download")
    parser.add_argument("github_owner", help="Your github owner")
    parser.add_argument("repository_name", help="Your repository name")
    parser.add_argument("branch_name", help="Your branch name in your GitHub repository")
    parser.add_argument(
        "--file_path", 
        help="Your branch name in your GitHub repository", 
        default=".research/research_history.json"
    )
    args = parser.parse_args()

    research_history = {
        "base_queries": "deep learning"
    }

    success = github_upload(
        github_owner=args.github_owner,
        repository_name=args.repository_name,
        branch_name=args.branch_name,
        research_history=research_history,
    )
    print(json.dumps({"success": success}))