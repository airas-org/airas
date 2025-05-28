import glob
import os
import shutil
import zipfile
from logging import getLogger

from airas.utils.api_client.github_client import GithubClient

logger = getLogger(__name__)


def _get_next_iteration_dir(save_dir: str) -> str:
    pattern = os.path.join(save_dir, "iteration_*")
    nums = [
        int(os.path.basename(p).split("_")[1])
        for p in glob.glob(pattern)
        if os.path.basename(p).split("_")[1].isdigit()
    ]
    next_index = max(nums, default=-1) + 1
    return os.path.join(save_dir, f"iteration_{next_index}")

def _parse_artifacts_id(artifacts_infos: dict, workflow_run_id: str) -> dict[str, int]:
    artifacts_id_dict = {}
    for artifacts_info in artifacts_infos["artifacts"]:
        if str(artifacts_info["workflow_run"]["id"]) == str(workflow_run_id):
            artifacts_id_dict[artifacts_info["name"]] = artifacts_info["id"]
    return artifacts_id_dict

def _save_zip_and_extract(zip_bytes: bytes, iteration_save_dir: str, artifact_name: str) -> None:
    zip_path = os.path.join(iteration_save_dir, f"{artifact_name}.zip")

    with open(zip_path, "wb") as f:
        f.write(zip_bytes)
    logger.info(f"Downloaded artifact saved to: {zip_path}")

    with zipfile.ZipFile(zip_path, "r") as zip_ref:
        zip_ref.extractall(iteration_save_dir)
    logger.info(f"Extracted artifact to: {iteration_save_dir}")

    if os.path.exists(zip_path):
        os.remove(zip_path)
        logger.info(f"ZIP file deleted: {zip_path}")


def _copy_images_to_latest_dir(source_dir: str, dest_dir: str) -> None:
    if os.path.exists(dest_dir):
        shutil.rmtree(dest_dir)
        logger.info(f"Removed exisiting images/: {dest_dir}")
    os.makedirs(dest_dir, exist_ok=True)

    for file_path in glob.glob(os.path.join(source_dir, "**", "*.pdf"), recursive=True):
        filename = os.path.basename(file_path)
        dest_path = os.path.join(dest_dir, filename)
        shutil.copyfile(file_path, dest_path)
        logger.info(f"Copied image to: {dest_path}")

def retrieve_github_actions_artifacts(
    github_owner: str,
    repository_name: str,
    workflow_run_id: str | int,
    save_dir: str,
    client: GithubClient | None = None, 
) -> tuple[str, str]:
    client = client or GithubClient()

    iteration_save_dir = _get_next_iteration_dir(save_dir)

    if os.path.exists(iteration_save_dir):
        shutil.rmtree(iteration_save_dir)
    os.makedirs(iteration_save_dir, exist_ok=True)

    response_artifacts_infos = client.list_repository_artifacts(
        github_owner, repository_name
    )
    
    artifacts_id_dict = _parse_artifacts_id(
        response_artifacts_infos, workflow_run_id
    )
    if not artifacts_id_dict:
        raise RuntimeError("No artifacts found for the specified run.")

    for name, artifacts_id in artifacts_id_dict.items():
        content = client.download_artifact_archive(
            github_owner, repository_name, artifacts_id
        )
        _save_zip_and_extract(content, iteration_save_dir, name)

    with open(os.path.join(iteration_save_dir, "output.txt"), "r") as f:
        output_text_data = f.read()
    with open(os.path.join(iteration_save_dir, "error.txt"), "r") as f:
        error_text_data = f.read()

    _copy_images_to_latest_dir(iteration_save_dir, os.path.join(save_dir, "images"))

    return (
        output_text_data,
        error_text_data,
    )