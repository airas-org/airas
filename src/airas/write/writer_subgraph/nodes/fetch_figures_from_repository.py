import logging
import os
import re

from airas.utils.api_client.github_client import GithubClient, GithubClientError

logger = logging.getLogger(__name__)


def _list_iteration_pdf_paths(
    github_owner: str, 
    repository_name: str,
    branch_name: str, 
    remote_dir: str, 
    client: GithubClient | None = None
) -> list[str]:
    client = client or GithubClient()
    try:
        branch_info = client.get_branch(
            github_owner, repository_name, branch_name
        )
        if branch_info is None:
            logger.warning(f"Branch not found: {branch_name}")
            return []
    except GithubClientError as e:
        logger.exception(f"GitHub API error: {e}")
        return []
    
    try:
        tree_sha = branch_info["commit"]["commit"]["tree"]["sha"]
        tree = client.get_a_tree(
            github_owner, repository_name, tree_sha
        )
        if tree is None or "tree" not in tree:
            logger.warning("Tree API returned empty result.")
            return []
    except GithubClientError as e:
        logger.exception(f"GitHub API error: {e}")
        return []

    return [
        item["path"]
        for item in tree["tree"]
        if item["type"] == "blob"
        and item["path"].startswith(remote_dir)
        and "/images/" in item["path"]
        and item["path"].lower().endswith(".pdf")
    ]

def _download_figures(
    github_owner: str, 
    repository_name: str, 
    branch_name: str, 
    blob_paths: list[str], 
    tmp_dir: str, 
    remote_dir: str = ".research", 
    client: GithubClient | None = None, 
) -> list[str]:
    client = client or GithubClient()
    downloaded: list[str] = []
    os.makedirs(tmp_dir, exist_ok=True)

    for path in blob_paths:
        try:
            binary = client.get_repository_content(
                github_owner,
                repository_name,
                file_path=path,
                branch_name=branch_name,
                as_="bytes",
            )
            if not isinstance(binary, (bytes, bytearray)):
                logger.warning(f"Failed to fetch binary for {path}")
                continue

            rel_path = path.removeprefix(remote_dir)
            local_path = os.path.join(tmp_dir, rel_path)

            parent_dir = os.path.dirname(local_path)
            os.makedirs(parent_dir, exist_ok=True)

            with open(local_path, "wb") as fp:
                fp.write(binary)

            downloaded.append(local_path)
            logger.info(f"Downloaded: {local_path}")
        except GithubClientError as e:
            logger.exception(f"GitHub API error: {e}")

    return downloaded

def _find_latest_images_dir(
    downloaded_paths: list[str], 
    tmp_dir: str, 
) -> str | None:
    _ITER_RE = re.compile(r"^iteration(\d+)$")

    latest_idx = -1
    iteration_indices = []

    for path in downloaded_paths:
        parts = os.path.normpath(path).split(os.sep)
        if len(parts) < 3:
            continue
        iter_part = parts[-3]
        match = _ITER_RE.fullmatch(iter_part)
        if match:
            iteration_indices.append(int(match.group(1)))

    if not iteration_indices:
        logger.warning("No valid iteration directories found in paths.")
        return None
    
    latest_idx = max(iteration_indices)
    latest_dir = os.path.join(tmp_dir, f"iteration{latest_idx}", "images")
    return latest_dir

def fetch_figures_from_repository(
    github_owner: str,
    repository_name: str,
    branch_name: str,
    tmp_dir: str,
    remote_dir: str = ".research", 
    client: GithubClient | None = None,
) -> str:
    client = client or GithubClient()

    blob_paths = _list_iteration_pdf_paths(
        github_owner=github_owner, 
        repository_name=repository_name, 
        branch_name=branch_name, 
        remote_dir=remote_dir, 
        client=client
    )
    if not blob_paths:
        logger.warning("No PDF figures found in the repository.")
        return []
    
    downloaded_paths = _download_figures(
        github_owner=github_owner,
        repository_name=repository_name,
        branch_name=branch_name,
        blob_paths=blob_paths,
        tmp_dir=tmp_dir,
        client=client, 
    )
    logger.info(f"Total figures downloaded: {len(downloaded_paths)}")

    latest_dir = _find_latest_images_dir(downloaded_paths, tmp_dir)
    if latest_dir is None:
        logger.exception("Failed to fetch figures from repository")
        return None 
    logger.info(f"Latest images dir: {latest_dir}")
    return latest_dir


if __name__== "__main__":
    latest_dir = fetch_figures_from_repository(
        github_owner="auto-res2", 
        repository_name="experiment_script_matsuzawa", 
        branch_name="base-branch", 
        tmp_dir="/workspaces/airas/tmp", 
    )
    print(f"latest_dir: {latest_dir}")