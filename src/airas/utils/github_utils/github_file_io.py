import base64
import json
import logging
import os
from typing import Any

from typing_extensions import TypedDict

from airas.utils.api_client.github_client import GithubClient

logger = logging.getLogger(__name__)


class ExtraFileConfig(TypedDict):
    upload_branch: str
    upload_dir: str
    local_file_paths: list[str]



def download_from_github(
    github_owner: str,
    repository_name: str,
    branch_name: str,
    input_path: str,
    client: GithubClient | None = None,
) -> dict[str, Any]:
    client = client or GithubClient()
    logger.info(f"[GitHub I/O] Downloading input from: {input_path}")
    data = client.read_file_bytes(
        github_owner,
        repository_name,
        branch_name,
        input_path,
    )
    file_bytes = base64.b64decode(data.get("content"))
    if not file_bytes:
        msg = f"Github file not found: {input_path}"
        logger.error(msg)
        raise FileNotFoundError(msg)
    try:
        decoded = json.loads(file_bytes.decode("utf-8"))
        if not isinstance(decoded, dict):
            raise ValueError("Decoded input is not a dictionary.")
        return decoded
    except Exception as e:
        raise ValueError(f"Failed to parse full-state JSON from {input_path}: {e}") from e

def upload_to_github(
    github_owner: str,
    repository_name: str,
    branch_name: str,
    output_path: str,
    state: dict[str, Any],
    client: GithubClient | None = None,
    *, 
    commit_message: str = "Upload file via AIRAS",
) -> bool:
    client = client or GithubClient()
    logger.info(f"[GitHub I/O] Uploading state to: {output_path}")
    return client.write_file_bytes(
        github_owner=github_owner,
        repository_name=repository_name,
        branch_name=branch_name,
        repository_path=output_path,
        file_content=_encode_content(state),
        commit_message=commit_message,
    )

def upload_extra_files(
    github_owner: str,
    repository_name: str,
    extra_files: list[ExtraFileConfig],
    client: GithubClient | None = None,
    commit_message: str = "Upload extra files via AIRAS",
) -> bool:
    client = client or GithubClient()
    all_ok = True
    for cfg in extra_files:
        for file_path in cfg["local_file_paths"]:
            try:
                with open(file_path, "rb") as f:
                    file_bytes = f.read()
                ok = client.write_file_bytes(
                    github_owner,
                    repository_name,
                    cfg["upload_branch"],
                    os.path.join(
                        cfg["upload_dir"], os.path.basename(file_path)
                    ).replace("\\", "/"),
                    file_bytes,
                    commit_message=commit_message,
                )
                all_ok &= ok
            except Exception as e:
                logger.warning(
                    f"Failed to read or upload extra file {file_path}: {e}",
                    exc_info=True,
                )
                all_ok = False
    return all_ok


def _encode_content(value: Any) -> bytes:
    match value:
        case bytes():
            return value
        case str() if os.path.isfile(value):
            with open(value, "rb") as f:
                return f.read()
        case str():
            return value.encode("utf-8")
        case _:
            return json.dumps(value, indent=2, ensure_ascii=False).encode("utf-8")