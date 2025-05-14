import argparse
import base64
import json
import logging
from typing import Any

from airas.utils.api_client.github_client import GithubClient

logger = logging.getLogger(__name__)


def github_download(
    github_owner: str, 
    repository_name: str, 
    branch_name: str, 
    file_path: str = ".research/research_history.json", 
    client: GithubClient | None = None, 
) -> dict[str, Any]:
    if client is None:
        client = GithubClient()
    logger.info(f"[GitHub I/O] Download: {github_owner}/{repository_name}@{branch_name}:{file_path}")

    try:
        blob = client.get_repository_content(
            github_owner=github_owner,
            repository_name=repository_name,
            file_path=file_path,
            branch_name=branch_name,
        )
        raw = base64.b64decode(blob["content"])
        return json.loads(raw) if raw else {}
    except FileNotFoundError as e:
        logger.error(f"State file not found – start with empty dict: {e}")
        raise 
    

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Download GitHub research history and print as JSON."
    )
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

    result = github_download(
        github_owner=args.github_owner,
        repository_name=args.repository_name,
        branch_name=args.branch_name,
        file_path=args.file_path,
    )
    print(json.dumps(result, indent=2))
