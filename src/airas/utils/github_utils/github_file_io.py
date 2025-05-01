import os
import base64
import json
import logging
from typing import Any, TypedDict
from airas.utils.api_request_handler import (
    fetch_api_data,
    retry_request,
)  # TODO: GithubClientの実装次第、変更します

logger = logging.getLogger(__name__)


class ExtraFileConfig(TypedDict):
    upload_branch: str
    upload_dir: str
    local_file_paths: list[str]


def _build_headers():
    return {
        "Accept": "application/vnd.github+json",
        "Authorization": f"Bearer {os.getenv('GITHUB_PERSONAL_ACCESS_TOKEN')}",
        "X-GitHub-Api-Version": "2022-11-28",
    }


def _download_file_bytes_from_github(
    github_owner: str,
    repository_name: str,
    branch_name: str,
    repository_path: str,
) -> bytes | None:
    url = f"https://api.github.com/repos/{github_owner}/{repository_name}/contents/{repository_path}"
    params = {"ref": branch_name}
    response = retry_request(
        fetch_api_data, url, headers=_build_headers(), params=params, method="GET"
    )
    if response and "content" in response:
        return base64.b64decode(response["content"])
    return None


def _upload_file_bytes_to_github(
    github_owner: str,
    repository_name: str,
    branch_name: str,
    repository_path: str,
    file_content: bytes,
    commit_message: str,
) -> bool:
    url = f"https://api.github.com/repos/{github_owner}/{repository_name}/contents/{repository_path}"
    existing = retry_request(
        fetch_api_data,
        url,
        headers=_build_headers(),
        params={"ref": branch_name},
        method="GET",
    )

    if isinstance(existing, dict) and "sha" in existing:
        sha = existing["sha"]
        logger.info(f"Updating existing file {repository_path} (sha={sha})")
    else:
        sha = None
        logger.info(f"Creating new file {repository_path}")

    data = {
        "message": commit_message,
        "branch": branch_name,
        "content": base64.b64encode(file_content).decode("utf-8"),
    }
    if sha:
        data["sha"] = sha

    try:
        response = retry_request(
            fetch_api_data, url, headers=_build_headers(), data=data, method="PUT"
        )
        if not isinstance(response, dict) or (msg := response.get("message")):
            logger.error(f"GitHub upload failed: {msg}")
            return False
        logger.info(
            f"GitHub upload succeeded: {repository_path} → branch {branch_name}"
        )
        return True

    except Exception as e:
        logger.error(
            f"Exception during GitHub upload to {repository_path} on branch {branch_name}: {e}",
            exc_info=True,
        )
        return False


def download_from_github(
    github_owner: str,
    repository_name: str,
    branch_name: str,
    input_path: str,
) -> dict[str, Any]:
    logger.info(f"[GitHub I/O] Downloading input from: {input_path}")
    file_bytes = _download_file_bytes_from_github(
        github_owner,
        repository_name,
        branch_name,
        input_path,
    )
    if not file_bytes:
        logger.error(f"GitHub file not found: {input_path}")
        raise FileNotFoundError(f"Required GitHub input not found: {input_path}")
    try:
        decoded = json.loads(file_bytes.decode("utf-8"))
        if not isinstance(decoded, dict):
            logger.error(f"Decoded input is not a dictionary: {input_path}")
            raise ValueError("Decoded input is not a dictionary.")
        return decoded
    except Exception as e:
        error_message = f"Failed to parse full-state JSON from {input_path}: {e}"
        logger.error(error_message)
        raise ValueError(error_message) from e


def upload_to_github(
    github_owner: str,
    repository_name: str,
    branch_name: str,
    output_path: str,
    state: dict[str, Any],
    extra_files: list[ExtraFileConfig] | None = None,
    commit_message: str = "Upload file via ResearchGraph",
) -> bool:
    logger.info(f"[GitHub I/O] Uploading state to: {output_path}")
    success = True

    try:
        file_bytes = _encode_content(state)
        ok = _upload_file_bytes_to_github(
            github_owner,
            repository_name,
            branch_name,
            output_path,
            file_bytes,
            commit_message=commit_message,
        )
        if not ok:
            success = False
    except Exception as e:
        logger.warning(f"Failed to upload state to {output_path}: {e}", exc_info=True)
        success = False

    if extra_files:
        for cfg in extra_files:
            for file_path in cfg["local_file_paths"]:
                try:
                    with open(file_path, "rb") as f:
                        file_bytes = f.read()
                    ok = _upload_file_bytes_to_github(
                        github_owner,
                        repository_name,
                        cfg["upload_branch"],
                        os.path.join(
                            cfg["upload_dir"], os.path.basename(file_path)
                        ).replace("\\", "/"),
                        file_bytes,
                        commit_message=commit_message,
                    )
                    if not ok:
                        success = False
                except Exception as e:
                    logger.warning(
                        f"Failed to read or upload extra file {file_path}: {e}",
                        exc_info=True,
                    )
                    success = False
    return success


def _encode_content(value: Any) -> bytes:
    if isinstance(value, str) and os.path.isfile(value):
        with open(value, "rb") as f:
            return f.read()
    elif isinstance(value, bytes):
        return value
    elif isinstance(value, str):
        return value.encode("utf-8")
    else:
        return json.dumps(value, indent=2, ensure_ascii=False).encode("utf-8")


def create_branch_on_github(
    github_owner: str,
    repository_name: str,
    new_branch_name: str,
    base_branch_name: str,
) -> None:
    ref_url = f"https://api.github.com/repos/{github_owner}/{repository_name}/git/ref/heads/{base_branch_name}"
    ref_response = retry_request(
        fetch_api_data, ref_url, headers=_build_headers(), method="GET"
    )
    if (
        not ref_response
        or "object" not in ref_response
        or "sha" not in ref_response["object"]
    ):
        logger.error(f"Failed to get base branch '{base_branch_name}' SHA")
        raise ValueError(f"Failed to get base branch '{base_branch_name}' SHA")

    base_sha = ref_response["object"]["sha"]
    create_url = (
        f"https://api.github.com/repos/{github_owner}/{repository_name}/git/refs"
    )
    payload = {
        "ref": f"refs/heads/{new_branch_name}",
        "sha": base_sha,
    }
    try:
        retry_request(
            fetch_api_data,
            create_url,
            headers=_build_headers(),
            data=payload,
            method="POST",
        )
        logger.info(
            f"Created new branch: {new_branch_name} based on {base_branch_name}"
        )
    except Exception as e:
        logger.warning(
            f"[GitHub] Branch creation failed or already exists: {new_branch_name} — {e}",
            exc_info=True,
        )
        raise
