import json
import logging
import time

from airas.core.types.github import GitHubConfig
from airas.core.types.research_history import ResearchHistory
from airas.infra.github_client import GithubClient

logger = logging.getLogger(__name__)


def github_upload(
    github_config: GitHubConfig,
    github_client: GithubClient,
    research_history: ResearchHistory,
    file_path: str = ".research/research_history.json",
    commit_message: str = "Update history via github_upload",
    wait_seconds: float = 3.0,
) -> bool:
    logger.info(
        f"[GitHub I/O] Upload: {github_config.github_owner}/{github_config.repository_name}@{github_config.branch_name}:{file_path}"
    )
    # Convert ResearchHistory to dict for JSON serialization with datetime handling
    research_history_dict = research_history.model_dump(exclude_none=True, mode="json")

    ok_json = github_client.commit_file_bytes(
        github_owner=github_config.github_owner,
        repository_name=github_config.repository_name,
        branch_name=github_config.branch_name,
        file_path=file_path,
        file_content=json.dumps(
            research_history_dict, ensure_ascii=False, indent=2
        ).encode("utf-8", errors="replace"),
        commit_message=commit_message,
    )
    if ok_json:
        print(
            f"Check here：https://github.com/{github_config.github_owner}/{github_config.repository_name}/blob/{github_config.branch_name}/{file_path}"
        )

    if wait_seconds > 0:
        time.sleep(wait_seconds)
    return ok_json
