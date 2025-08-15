import json
import logging
import time

from airas.services.api_client.github_client import GithubClient
from airas.types.github import GitHubRepositoryInfo
from airas.types.research_history import ResearchHistory

logger = logging.getLogger(__name__)


def github_upload(
    github_repository_info: GitHubRepositoryInfo,
    research_history: ResearchHistory,
    file_path: str = ".research/research_history.json",
    commit_message: str = "Update history via github_upload",
    wait_seconds: float = 3.0,
    client: GithubClient | None = None,
) -> bool:
    if client is None:
        client = GithubClient()

    logger.info(
        f"[GitHub I/O] Upload: {github_repository_info.github_owner}/{github_repository_info.repository_name}@{github_repository_info.branch_name}:{file_path}"
    )
    # Convert ResearchHistory to dict for JSON serialization
    research_history_dict = research_history.model_dump(exclude_none=True)

    ok_json = client.commit_file_bytes(
        github_owner=github_repository_info.github_owner,
        repository_name=github_repository_info.repository_name,
        branch_name=github_repository_info.branch_name,
        file_path=file_path,
        file_content=json.dumps(
            research_history_dict, ensure_ascii=False, indent=2
        ).encode(),
        commit_message=commit_message,
    )
    if ok_json:
        print(
            f"Check here：https://github.com/{github_repository_info.github_owner}/{github_repository_info.repository_name}/blob/{github_repository_info.branch_name}/{file_path}"
        )

    if wait_seconds > 0:
        time.sleep(wait_seconds)
    return ok_json
